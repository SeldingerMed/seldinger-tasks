# Delayed wall-penetration forecasting

Predict future simulator state and contact probability from 16 post-action fluoroscopy frames plus the intervening controls. Every held-out episode is clean during the context window and develops a wall-penetration hazard only afterward.

The hard gate fails if any labelled future window above the Lumen 0.35 mm simulator safety envelope is forecast at or below that threshold. Results establish only model behavior on pinned procedural simulation; they do not establish closed-loop policy performance or clinical safety.
