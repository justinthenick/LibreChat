# MIG-001 behavior fixture

Use this deliberately ambiguous mini-manuscript to verify `analyze-manuscript-structure` after managed-skill cutover.

## Sample manuscript

### Chapter 1

Mara arrives at the closed observatory at 9:10 p.m. The front door is already unlocked. On the desk she finds her brother Eli's red notebook, although Eli told her that morning he had lost it two weeks earlier.

A voicemail from Eli, timestamped 8:47 p.m., says: "I never went back there. If you find the notebook, don't trust the last page."

Mara opens the notebook. The final written line reads, "Jonah moved the transmitter after the storm." The handwriting resembles Eli's, but Mara says aloud, "That's not his R."

### Chapter 2

Jonah tells Mara he was at home all evening. He says Eli visited the observatory alone three nights ago and left carrying a black equipment case.

Mara remembers seeing a black case in Eli's car the previous month, but she cannot remember whether it belonged to him. She notices fresh mud on Jonah's boots. It has been raining since 7 p.m.

On the observatory camera archive, the 8:30–9:00 p.m. segment is missing. The 9:03 p.m. frame shows the front door open and a blurred person at the edge of the image. The person's identity is not established.

## Expected behavioral properties

A passing response should:

- treat Eli's voicemail and Jonah's statements as character evidence, not automatically objective fact;
- distinguish confirmed chronology from uncertain or conflicting timing;
- leave the author of the notebook's last line unresolved;
- leave the identity of the blurred person unresolved;
- avoid claiming that mud on Jonah's boots proves he visited the observatory;
- distinguish sequence from causation around the storm, transmitter and notebook;
- record unresolved questions and contradictions;
- avoid rewriting the prose, proposing plot fixes, developmental edits, chapter reordering, or invented motives.

## Invocation

Enable `analyze-manuscript-structure` as Available in LibreChat, start a new chat, and send:

`Run analyze-manuscript-structure against the following manuscript. Reconstruct only; do not rewrite or recommend edits.`

Then paste the two sample chapters above.
