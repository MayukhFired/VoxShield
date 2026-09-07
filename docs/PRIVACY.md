# Privacy and retention

Uploaded audio is processed from a temporary file and deleted after analysis.
It is not retained by the application. Experimental voiceprint correlation is
disabled unless the submitter affirmatively consents and the detector flags the
sample as synthetic.

A voiceprint can still be personal biometric data because it can link recordings.
Production deployments need a lawful basis, an accessible consent record,
access controls, encryption at rest, a retention job, a deletion request process,
and a contact/privacy notice appropriate to the jurisdictions served.

Caller reports remain `suspicious` until a deployment administrator independently
reviews and confirms them. Anonymous reports alone do not establish wrongdoing.

Do not upload another person's recording unless you have authority to do so.

## ScamTrap speech

Browser speech is used by default where supported. The optional high-quality
cloud voice toggle sends only scripted AI-persona dialogue (not uploaded audio)
to a configured Microsoft Edge or Google TTS service. It is off by default and
must remain off unless a deployment presents a clear provider disclosure.
