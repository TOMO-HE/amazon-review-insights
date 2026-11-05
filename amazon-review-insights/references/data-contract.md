# File and annotation contract

The scripts use JSON with `schema_version: 1`. They do not call a model or send text to a remote service. The executing AI reads prepared records and writes annotations. No API key is required by these helpers.

## Input mapping

Recognized canonical fields: `id`, `product`, `variant`, `title`, `body`, `country`, `date`, `rating`, `verified`, `helpful`, `photo`, `video`. Typical English and Chinese headers are recognized. Supply `--mapping` to override, for example:

```json
{"body":"Review Text","rating":"Stars","product":"ASIN"}
```

Dates accept ISO dates, Excel dates and English Amazon `Reviewed in … on Month D, YYYY`. Unrecognized dates remain null with a warning. Country may be derived from that Amazon date text but never from the language or marketplace. Rating accepts numeric values and English/Chinese star formats; blank or invalid values remain null. Preparation omits author names and avatar URLs from publication data.

## Annotation example

See the runnable synthetic example at the repository's `examples/annotations.json`. Use the **actual prepared fingerprint**, not the example fingerprint.

```json
{
  "schema_version": 1,
  "review_set_sha256": "copy fingerprint from prepared.json",
  "report": {
    "title": "产品评论洞察",
    "summary": "根据已标注样本归纳的中文概述。",
    "recommendations": [
      {"text":"分别测各亮度下的续航。","support_ids":["review-1"]}
    ]
  },
  "decisions": [
    {
      "id":"review-1",
      "status":"analyzed",
      "summary":"补光好，但连续拍摄时续航不足。",
      "observations":[
        {"kind":"aspect","label":"续航","sentiment":"negative","evidence":[{"field":"body","quote":"dies in twenty minutes"}]},
        {"kind":"scenario","label":"视频录制","evidence":[{"field":"body","quote":"recording videos"}]}
      ]
    },
    {"id":"review-2","status":"excluded","reason":"正文主要描述另一种产品。","observations":[]}
  ]
}
```

- `kind` is `aspect`, `scenario`, `motive` or `need`. Labels should be concise Chinese. `need` is an explicit request; inferred needs are recommendations, never relabeled as direct requests.
- An aspect requires `sentiment`: `positive`, `negative`, `neutral`. Other kinds omit sentiment. Distinct kinds are not interchangeable.
- Each observation needs one or more nonempty literal quotations from `title` or `body`. Whitespace is normalized for matching; invented translations do not qualify. The validator checks quote presence, not whether the interpretation is correct. Read and assess semantic entailment yourself.
- One decision per unique prepared ID. `analyzed` may have zero observations if no concrete theme is present. An exclusion needs a reason and no observations. Missing decisions are pending, not analyzed negatives or zeros.
- Duplicate `(kind,label,sentiment)` observations within a review must be combined with multiple evidence entries. The same review can support opposite polarities separately.
- Recommendations need at least one analyzed `support_id`; generated advice is not a measured finding. Summary prose needs manual factual review.
- The fingerprint locks annotations to exact normalized source records, provenance and quality findings. Re-prepare after source edits and regenerate/reconcile annotations. Never change the fingerprint just to bypass stale data checks.
- `--allow-partial` permits publishing an explicitly marked preliminary report. All metrics then use only analyzed records and the report displays pending/excluded counts.

Prepared and annotated working files may contain customer text. Do not commit them to a public repository by default. The shipped example data is fictional.
