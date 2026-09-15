# 🍽️ SkyCity Auckland — Multi-Channel Profitability Intelligence

A Streamlit dashboard that compares **In-Store, Uber Eats, DoorDash, and Self-Delivery**
channel economics for SkyCity Auckland's restaurant & bar portfolio — net profit, margin %,
commission drag, cost waterfalls, cuisine/segment heatmaps, and a live what-if simulator.

## Project structure

```
skycity_project/
├── app/
│   └── app.py                 # Streamlit application (main entry point)
├── data/
│   └── restaurants.csv        # Source dataset (1,696 restaurant-branch rows)
├── docs/
│   ├── SkyCity_Research_Paper.docx
│   └── SkyCity_Executive_Summary.docx
├── .streamlit/
│   └── config.toml            # Dark theme configuration
├── requirements.txt
└── README.md
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

The app opens at `http://localhost:8501`.

## Deploy for free — Streamlit Community Cloud (recommended, ~2 minutes)

1. Create a new GitHub repository and push this entire `skycity_project/` folder to it.
2. Go to **https://share.streamlit.io** → sign in with GitHub → **"New app"**.
3. Select your repo, branch `main`, and set **Main file path** to `app/app.py`.
4. Click **Deploy**. No secrets or API keys are required — the dataset ships in `data/`.
5. You'll get a public URL like `https://skycity-auckland.streamlit.app`.

## Deploy alternatives

- **Render.com / Railway.app**: create a new Web Service from the repo, build command
  `pip install -r requirements.txt`, start command `streamlit run app/app.py --server.port $PORT --server.address 0.0.0.0`.
- **Docker** (any cloud):
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY . .
  RUN pip install -r requirements.txt
  EXPOSE 8501
  CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
  ```
- **Hugging Face Spaces**: choose "Streamlit" as the Space SDK, push this repo, set app file
  to `app/app.py`.

## Dashboard modules

| Tab | What it shows |
|---|---|
| Overview | Revenue vs. profit by channel, order mix, headline margin comparison |
| Channel Profitability | Net profit per order, absolute profit vs. margin efficiency, most efficient channel per restaurant |
| Cost Breakdown | Revenue → Net Profit waterfall per channel, commission drag index, self-delivery breakeven curve |
| Cuisine & Segment | Margin heatmaps by cuisine, segment, subregion; margin-resilient vs. fragile categories |
| What-If Simulator | Sidebar sliders re-price commission % and delivery cost/order live across all charts |
| Risk & Volatility | Coefficient-of-variation volatility score, margin distributions (box plots), loss-prone restaurant counts |
| Data Explorer | Full filtered restaurant-level table with CSV export |

## Filters (sidebar)

Cuisine Type · Segment · Subregion · Restaurant name — all filters combine (AND logic) and
propagate to every chart and KPI on the page.

## Data dictionary

See the CSV header / research paper Appendix A for full column definitions. Net profit
formulas used (validated against the source data during EDA):

- `InStoreNetProfit = InStoreRevenue × (1 − COGSRate − OPEXRate)`
- `UberEatsNetProfit = UberEatsRevenue × (1 − COGSRate − OPEXRate − CommissionRate)`
- `DoorDashNetProfit = DoorDashRevenue × (1 − COGSRate − OPEXRate − CommissionRate)`
- `SelfDeliveryNetProfit = SelfDeliveryRevenue × (1 − COGSRate − OPEXRate) − SD_DeliveryTotalCost`

## License / attribution

Prepared as a Unified Mentor capstone project on SkyCity Auckland Restaurants & Bars.
