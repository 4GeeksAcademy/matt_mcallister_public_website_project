import type { NextFunction, Request, Response } from "express";
import { ApiError } from "../types/errors.js";

export const notFoundHandler = (_req: Request, res: Response) => {
  res.status(404).json({
    error: {
      code: "NOT_FOUND",
      message: "The requested resource was not found.",
    },
  });
};

export const errorHandler = (
  err: unknown,
  _req: Request,
  res: Response,
  _next: NextFunction,
) => {
  if (err instanceof ApiError) {
    res.status(err.statusCode).json(err.toJSON());
    return;
  }

  console.error("Unhandled server error:", err);
  res.status(500).json({
    error: {
      code: "INTERNAL_ERROR",
      message:
        "Something went wrong on our side. Please try again in a moment or contact comercial@trackflow.com for help.",
    },
  });
};
