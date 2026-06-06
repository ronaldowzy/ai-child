# Public Redaction Notes

The private development repository previously included raw real-device prompt
trace material used for debugging family beta behavior. That material is not
appropriate for a public repository because raw prompts and model traces may
contain child profile details, parent notes, device/session identifiers, and
private family context.

For the public branch:

- raw prompt appendices are removed;
- documentation should point to sanitized summaries only;
- tests should use synthetic child names and synthetic media;
- any future real-device QA evidence must be redacted before commit.

If this branch is used to make GitHub public, review Git history as well as the
current working tree. A normal delete commit removes the file from the current
tree but not from historical commits.
