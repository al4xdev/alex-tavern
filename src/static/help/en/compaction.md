# 🗜️ Story compaction

A long adventure can grow beyond the amount of text the AI can read at once. Compaction prevents this by turning older events into smaller memories while keeping recent scenes complete.

## A simple example

Think of the adventure as a book with many chapters:

- recent chapters remain written in full;
- older chapters become a summary of what happened in the world;
- each character keeps a separate note containing only their own memories;
- the story continues normally from those memories.

Compaction does not change the current scene, character moods, or who you control.

## Automatic compaction

When it is **on**, the app watches how much of the AI's reading space the next scene will use. If the story is approaching your chosen limit, it summarizes old events before calling the Narrator.

A turn containing only a private thought does not trigger compaction. The check waits for the next speech, action, or Narrator advance.

## What the percentage changes

The percentage says how much reading space may be used before summarizing:

- **Move it down:** summarize earlier. The Historian works more often, but more room remains for the next scene.
- **Keep it near 80%:** a comfortable balance for most adventures.
- **Move it up:** wait longer. The Historian works less often, but the next scene runs closer to the reading limit.

This percentage is a practical estimate, not an exact provider token count.

## Manual compaction

The 🗜️ button in the action menu runs the same operation immediately. Its bar shows work that actually finished: the world summary, each character memory, and the safe session save.

If there are not enough old events yet, nothing changes.

## Can I undo it?

Yes. Every completed compaction creates a numbered checkpoint. The 🧯 button undoes the newest compaction first and can be used repeatedly to walk through older ones.

Turns played after a compaction are preserved. Checkpoints remain with the session until it is deleted.

## What each agent may remember

- The Narrator receives the public world summary without private thoughts.
- Each character receives only their own note and their own old thoughts.
- A character never receives another character's note or private thoughts.

If automatic compaction fails, the app keeps history unchanged and continues the turn with the available recent window.
