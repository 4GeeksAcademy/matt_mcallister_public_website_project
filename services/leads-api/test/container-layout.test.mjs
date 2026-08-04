import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { test } from "node:test";

const serverPath = "dist/services/leads-api/src/server.js";
const corePath = "dist/packages/trackflow-core/src/index.js";

test("compiled server preserves and loads the canonical core module", async (t) => {
  assert.equal(existsSync(serverPath), true, `missing ${serverPath}`);
  assert.equal(existsSync(corePath), true, `missing ${corePath}`);

  const core = await import(`../${corePath}`);
  const snapshot = core.buildOperationsAnalysis(
    core.demoProducts,
    core.demoShipments,
    core.demoCarriers,
  );
  assert.equal(snapshot.inventory.totalUnits, 173);

  const port = 41000 + (process.pid % 10000);
  const server = spawn(process.execPath, [serverPath], {
    env: { ...process.env, PORT: String(port) },
    stdio: ["ignore", "pipe", "pipe"],
  });
  t.after(() => server.kill());

  const url = `http://127.0.0.1:${port}/api/executive-snapshot`;
  let response;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (server.exitCode !== null) {
      throw new Error(`compiled server exited with code ${server.exitCode}`);
    }
    try {
      response = await fetch(url);
      break;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
  }

  assert.ok(response, "compiled server did not start");
  assert.equal(response.status, 200);
  assert.equal((await response.json()).data.inventory.totalUnits, 173);
});
