import cors from "cors";
import express from "express";
import { errorHandler, notFoundHandler } from "./middleware/errorHandler.js";
import executiveSnapshotRouter from "./routes/executiveSnapshot.js";
import leadsRouter from "./routes/leads.js";

const app = express();
const port = Number(process.env.PORT) || 4000;

app.use(
  cors({
    origin: [
      "http://localhost:3000",
      "http://localhost:3001",
      "http://127.0.0.1:3000",
      "http://127.0.0.1:3001",
    ],
  }),
);
app.use(express.json());

app.get("/health", (_req, res) => {
  res.status(200).json({ status: "ok" });
});

app.use("/api/leads", leadsRouter);
app.use("/api/executive-snapshot", executiveSnapshotRouter);

app.use(notFoundHandler);
app.use(errorHandler);

app.listen(port, () => {
  console.log(`TrackFlow API listening on http://localhost:${port}`);
});
