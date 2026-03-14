# Game Design Insights

### 1. The "Dead Zones" in Ambrose Valley
* **Observation:** High-tier loot markers in the Northwest quadrant show zero player traffic in 80% of matches.
* **Evidence:** The heatmap shows heavy "red" clusters in the center, but the Northwest remains "blue" (empty) despite loot availability.
* **Actionable Item:** Introduce a "High-Tier Extraction Point" or a landmark in that area to pull players away from the center "meat-grinder."
* **Metric Affected:** Player Distribution & Average Match Length.

### 2. Bot Navigation Bottlenecks
* **Observation:** Bots (Numeric IDs) show a pattern of "jittering" or getting stuck at the edges of Grand Rift.
* **Evidence:** Filtering for "Bots Only" shows paths that stop abruptly at specific coordinate clusters without a corresponding `Killed` event.
* **Actionable Item:** Update the navigation mesh for bots specifically around steep terrain or cliff edges.
* **Value to Designer:** Higher quality "filler" combat for humans, making the world feel more alive.

### 3. Storm Timing Choke-Points
* **Observation:** A surge in `KilledByStorm` events occurs at the narrow canyon passage in Lockdown.
* **Evidence:** Timeline playback shows 4-5 players dying simultaneously at this passage as the storm circle closes.
* **Actionable Item:** Widening the passage or adding a vertical "jump pad" could reduce the frustration of "unavoidable" storm deaths.
* **Value to Designer:** Improves player retention by removing "unfair" death mechanics.
