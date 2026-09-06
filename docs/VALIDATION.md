# Validation plan

VoxShield is a research prototype. Do not use its output as the sole basis for
law-enforcement, banking, account-access, or identity decisions.

## Before claiming detection accuracy

1. Freeze a model version, its weights checksum, preprocessing parameters, and
   decision threshold.
2. Evaluate on a held-out ASVspoof partition and on a separately collected
   real-world set. Keep speakers, generators, and recordings disjoint from
   training data.
3. Report EER, ROC-AUC, false-accept rate, false-reject rate, and 95% confidence
   intervals. Break results down by language, device, codec, background noise,
   and previously unseen generators.
4. Calibrate probabilities on a validation set and return `inconclusive` when
   the score is near the decision boundary or audio quality is insufficient.
5. Run regression tests against a versioned, consented evaluation fixture set
   before every release.

## Voiceprint correlation

The current voiceprint feature extractor is experimental. Validate it only on
consented, labeled source-speaker / converted-speech pairs. Select any matching
threshold using a held-out set and publish false-match and false-non-match rates.
Never describe a similarity result as identifying a person or proving criminal
activity.

## Dataset governance

Maintain `data/DATASET_MANIFEST.csv` outside public releases with source,
license, consent status, speaker-use restrictions, generator, language, and
split for every file. Do not add recordings whose redistribution or biometric
analysis is not authorized.
