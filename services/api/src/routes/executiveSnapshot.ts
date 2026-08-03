import { Router } from "express";
import {
  buildExecutiveSnapshot,
  milestone2SampleInput,
} from "../../../../packages/shared/business-logic/milestone2.js";
import { ApiError } from "../types/errors.js";

const router = Router();

router.get("/", (_req, res, next) => {
  try {
    const snapshot = buildExecutiveSnapshot(milestone2SampleInput);
    res.status(200).json({ data: snapshot });
  } catch (error) {
    next(
      new ApiError(
        500,
        "SNAPSHOT_ERROR",
        "We could not load the executive snapshot right now. Please refresh the page or try again later.",
      ),
    );
  }
});

export default router;
