# Analysis method

## Schema discovery

Preparation reads values, not Excel formulas. Missing cached values are missing data, not zero. Confirm the review text column instead of concatenating usernames, seller replies and product descriptions. Do not silently discard unrated records; they remain part of theme analysis but not the star-average denominator. Invalid ratings, dates and unknown-country fields belong in the quality summary.

IDs deduplicate repeated exports of the same review. Conflicting duplicate IDs require inspection; preparation flags them, and rendering blocks until the source is resolved. Identical short text with distinct IDs is not sufficient evidence of duplication. Without a supplied ID, each row has a stable source-based ID and is retained. Audit attribution remains source basename, sheet and row; original files remain unchanged.

Several ASINs may be variants or unrelated products. Preserve ASIN/product and variant fields. Do not label them as one parent listing unless supplied data or the user confirms that relationship. Missing country/date information stays unknown. Choose a US-only analysis only if requested or useful, and label it separately.

## Semantic coding

Read the title and body together, including multilingual text and later updates. Quote the latest stated experience when a review revises its original assessment. Use `mixed` only as an interpretation in prose: encode separate positive and negative observations when both survive, then count the review once per polarity.

Suggested starting taxonomy, adjusted to the actual product:

| Dimension | Example labels | Do not conflate |
|---|---|---|
| Performance | illumination, clarity, runtime, capacity | subjective comparison with measured specifications |
| Usability | setup, adjustability, controls, portability | intended use with actual use |
| Reliability | power-on failure, charge failure, breakage | short battery runtime with battery failure |
| Compatibility | magnetic hold, camera clearance, device fit | weak magnet, failed adhesive, overloaded hinge |
| Experience | mirror visibility, audible whine, rattle, heat | separate failure mechanisms |
| Fulfilment | missing cable, missing adapter, damaged arrival | missing part with not included by design |

Begin with a small stratified sample to discover labels, then code all records using the same definitions. Preserve minority issues even if they do not reach a top-five card. Split a topic only if it changes the interpretation or proposed action. Generic “Love it” can be analyzed with zero aspect observations; it is not evidence for battery, brightness or quality.

Scenario labels describe what the review mentions, including intended and described uses; clarify that scope. Purchase motives require a buying/choosing/replacing/gifting narrative. Do not label a user “student”, “photographer” or “content creator” as an occupation merely because they record videos. Report task signals instead.

For each record, include a short Chinese summary of its meaning when useful; it is not a literal translation. Keep source quotes and the original body visible. Do not call rewritten summaries original quotations.

## Quantification and interpretation

For selected analyzed reviews S, topic-positive = unique IDs in S with positive evidence for that topic. Topic-negative follows the same rule. Topic mention = union of all polarities. Top-card percentages use |S|. A within-topic sentiment rate must instead label its topic-specific denominator explicitly. Counts across themes can exceed |S|.

Keep “not mentioned”, “unavailable”, “neutral” and “negative” distinct. Excluded records stay accessible in the audit trail. Image/video counts are presence of links, not evidence that media has been inspected. Verified Purchase and media categories overlap; no part-to-whole donut. Vine is unavailable unless an explicit Vine field is provided.

Monthly charts describe the supplied sample only. If export ordering, truncation or coverage is unknown, do not infer sales, population defect rates, market share, a quality improvement trend or statistical causation. Recommendations may prioritize low-frequency, high-impact issues (such as audio interference during filming) with an explicit reason.

## Learning from a reference report

Compare four layers separately: data scope; labeling/taxonomy; aggregation; presentation. Similar themes validate neither report's percentages. A rival report's gender proportions, color requests and compatibility statements need independent evidence. Device-specific claims from one reviewer remain reported experiences until tested or confirmed. Explain justified departures from the reference rather than forcing unsupported cards into the layout.
