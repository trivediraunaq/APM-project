**Purpose:** This proves you understand the "Why" and the "How" behind your technical decisions.

# System Architecture

## Tech Stack Selection
* **Python/Streamlit:** Chosen for rapid prototyping. It allows for a reactive UI that handles large Parquet datasets without the overhead of a React/Node.js boilerplate.
* **Plotly:** Used for the visualization layer because it supports interactive hardware-accelerated rendering of thousands of data points (scatter and line traces) over static image backgrounds.
* **Pandas/PyArrow:** Essential for parsing the `.nakama-0` Parquet files efficiently.

## Coordinate Mapping Logic (The "Tricky Part")
The core challenge was translating 3D world space coordinates $(x, z)$ into 2D image pixel coordinates $(1024 \times 1024)$.

1.  **Normalization:** I calculated the UV coordinates by subtracting the map origin and dividing by the map scale provided in the README.
2.  **Pixel Translation:** Normalized values were scaled to 1024 pixels.
3.  **Axis Correction:** Since game engines often use a "bottom-up" Z-axis and images use a "top-down" Y-axis, I inverted the vertical axis ($1 - v$) to ensure deaths and loot appeared in the correct geographic locations.

## Data Handling & Assumptions
* **Event Decoding:** Decoded `event` column from bytes to UTF-8.
* **Bot Identification:** Assumed any `user_id` that is strictly numeric is a Bot, while UUIDs are human players.
* **Missing Data:** Handled the partial data for February 14th by allowing the UI to gracefully filter empty matches without crashing.

## Trade-offs
| Decision | Trade-off | Reason |
| :--- | :--- | :--- |
| **Local Parquet Loading** | Slower initial boot vs. Cloud Database | Given the 5-day timeline and small dataset (~8MB), local processing was more reliable for a portable tool. |
| **2D Top-Down View** | Simplicity vs. 3D Elevation | A 2D heatmap is more actionable for a Level Designer to identify "choke points" than a complex 3D view. |
