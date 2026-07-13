# Thorn and Lyra manual playtest script

Use the built-in **`thorn-lyra`** preset and keep **Thorn (`C1`)** as the
controlled character. The script starts in Old Mork's Tavern and follows one
continuous story.

For each numbered row, paste **Speech** into the speech field and **Action**
into the action field, choose the indicated **Force speaker** value, and submit
the turn. Wait for the complete response before continuing. The expected outcome
is a testing checkpoint, not text that the model must reproduce exactly.

|    Step | Speech (Thorn)                                                              | Action (Thorn)                                                                                           | Force speaker | Expected outcome / checkpoint                                                                                                                                                                                         |
| ------: | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|       1 | Keep your voice down, Lyra. Someone has been watching us since we entered   | I set the faintly glowing medallion on the table, but keep two fingers over it while I scan the tavern   | Lyra (C2)     | Establish the medallion mystery and produce a complete Narrator + Character turn.                                                                                                                                     |
|       2 | Tell me what the medallion is doing, in plain words                         | I slide the medallion toward Lyra and turn my chair so I can watch both the door and the hooded stranger | Lyra (C2)     | Lyra should examine the object while Thorn remains suspicious of magic.                                                                                                                                               |
|       3 | You in the hood. If you want something, ask before my patience runs out     | I raise one hand toward the stranger without drawing my sword                                            | Automatic     | Exercise natural speaker routing and introduce an NPC or environmental reaction.                                                                                                                                      |
|       4 | Lyra, stop. That symbol belongs to the old Iron Guard                       | I pull the medallion back and study its markings under the candlelight                                   | Narrator      | Reveal Thorn's connection to the symbol without forcing a Character response.                                                                                                                                         |
|       5 | My brother carried this mark on his last patrol. Where did you find it?     | I lean across the table, staring at Lyra more intensely than I intended                                  | Lyra (C2)     | Invite a relationship or mood change tied to Thorn's guilt.                                                                                                                                                           |
|       6 | Mork, bar the door. Nobody leaves until we understand what is happening     | I stand, move between the patrons and Lyra, and rest my hand on the hilt of my sword                     | Automatic     | Encourage visible scene changes such as the door, crowd, or lighting.                                                                                                                                                 |
|       7 | If the forest sent this thing here, waiting inside will not make us safer   | I wrap the medallion in a scrap of cloth and secure it inside my armor                                   | Lyra (C2)     | Connect the tavern scene to Lyra's knowledge of the corrupted northern forest.                                                                                                                                        |
|       8 | Pack only what you need. We leave through the kitchen                       | I check the rear corridor for an ambush and signal Lyra to follow                                        | Lyra (C2)     | Begin a location transition and exercise mutable physical facts.                                                                                                                                                      |
|       9 | Stay close. The rain will hide us, but it will hide anyone following us too | I push open the kitchen exit and step into the alley, shielding my eyes from the rain                    | Automatic     | Move outdoors and update location, weather exposure, and present details.                                                                                                                                             |
|      10 | There, by the drain. The same symbol again                                  | I crouch beside a fresh mark scratched into the stone and compare it with the medallion                  | Lyra (C2)     | Create a visually clear scene fact suitable for state/debug inspection.                                                                                                                                               |
|      11 | Can you trace the magic without touching it?                                | I hold the wrapped medallion near the scratched symbol while keeping it out of Lyra's reach              | Lyra (C2)     | Test Lyra's magic-as-science personality and another mood transition.                                                                                                                                                 |
|      12 | Then we follow the trail, but we do it my way: slowly                       | I lead us north through the narrow streets, checking every rooftop and doorway                           | Automatic     | Advance the journey while allowing natural routing.                                                                                                                                                                   |
|      13 | That bell has rung three times, but the tower is empty                      | I stop beneath the abandoned watchtower and listen for movement above us                                 | Narrator      | Exercise a narration-only continuation with a new landmark.                                                                                                                                                           |
|      14 | Lyra, light the smallest spell you have. No fireworks                       | I draw my sword and enter the watchtower ahead of her                                                    | Lyra (C2)     | Prompt light and interior-state changes plus a Character response.                                                                                                                                                    |
|      15 | These are Iron Guard orders. My unit was sent into the forest on a lie      | I lift a water-damaged dispatch from the floor and read it beside Lyra's light                           | Lyra (C2)     | Add a durable plot revelation for later compaction.                                                                                                                                                                   |
|      16 | I blamed myself for years. Someone arranged that ambush                     | My sword lowers as I hand the dispatch to Lyra, no longer hiding that my hands are shaking               | Lyra (C2)     | Encourage a strong, visible mood/relationship update.                                                                                                                                                                 |
|      17 | We finish this. At dawn, we take the north road                             | I fold the dispatch, place it beside the medallion, and search the room for supplies                     | Automatic     | Establish a concrete plan and inventory/scene facts.                                                                                                                                                                  |
|      18 | Do you hear scratching behind that wall?                                    | I press my ear to the loose boards, then motion for Lyra to stand back                                   | Lyra (C2)     | Set up immediate danger and test suspense continuity.                                                                                                                                                                 |
|      19 | On my count, break the ward. I will handle whatever comes through           | I brace in front of Lyra with my sword raised and count down from three                                  | Lyra (C2)     | Produce an action-heavy complete turn and likely state changes.                                                                                                                                                       |
|      20 | That map leads straight into the corrupted forest. So does the truth        | I spread the hidden map across a crate, mark our route at first light, and finally sheath my sword       | Lyra (C2)     | Close the test sequence with facts worth retaining in the story summary.                                                                                                                                              |
| Compact | _(leave both input fields unchanged; do not submit another turn)_           | Click **Compact session** (🗜️) and capture the progress bar while it is partially filled                 | N/A           | A real compaction should occur because the session has more than 8 distinct turns. After completion, verify that only the 8 most recent turns remain in active history and that the story still continues coherently. |

## Suggested README capture points

- **After step 1 or 2:** capture a full turn with Narrator and Lyra responses.
- **After step 6, 9, 14, or 16:** inspect mood and scene state. If both changed
  in the latest turn, this is a good point to record **Undo**, then use
  **Retry** to restore the story before continuing.
- **Any time after step 2:** open the raw log and look for adjacent `narrator`
  and `character:Lyra` entries sharing one turn number.
- **Before any later step:** open **Suggest** long enough to capture all three
  candidate speech/action pairs, then close it and continue with the scripted
  row.
- **After step 20:** perform the Compact row. Capture the button during its
  simulated progress animation, before the request finishes.

## Post-compaction smoke check

After the compact operation succeeds, submit this optional continuation to
confirm that the summary preserves the old plot while the recent window remains
verbatim:

- **Speech:**
  `Before we leave, tell me the three facts we cannot afford to forget.`
- **Action:**
  `I point in turn to the medallion, the Iron Guard dispatch, and the route marked on the hidden map.`
- **Force speaker:** Lyra (`C2`)
