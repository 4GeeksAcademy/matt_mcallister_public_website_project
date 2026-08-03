import bcrypt from "bcryptjs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

type UserRecord = {
  id: string;
  email: string;
  passwordHash: string;
};

type ResetTokenRecord = {
  jti: string;
  userId: string;
  expiresAt: number;
};

type AuthStoreData = {
  users: UserRecord[];
  resetTokens: ResetTokenRecord[];
};

const authStoreFilePath =
  process.env.AUTH_STORE_FILE?.trim() ||
  path.join(process.cwd(), ".data", "auth-store.json");

let storeWriteQueue: Promise<void> = Promise.resolve();

const defaultDemoEmail = process.env.AUTH_DEMO_USER_EMAIL?.trim().toLowerCase() || "demo@trackflow.local";
const defaultDemoPassword = process.env.AUTH_DEMO_USER_PASSWORD || "ChangeMe123!";

function createDemoUser(): UserRecord {
  return {
    id: "user_demo_1",
    email: defaultDemoEmail,
    passwordHash: bcrypt.hashSync(defaultDemoPassword, 12),
  };
}

function getDefaultStore(): AuthStoreData {
  return {
    users: [createDemoUser()],
    resetTokens: [],
  };
}

function normalizeStore(store: Partial<AuthStoreData> | null | undefined): AuthStoreData {
  const users = Array.isArray(store?.users)
    ? store.users.filter(
        (user): user is UserRecord =>
          Boolean(
            user &&
              typeof user.id === "string" &&
              typeof user.email === "string" &&
              typeof user.passwordHash === "string",
          ),
      )
    : [];

  const resetTokens = Array.isArray(store?.resetTokens)
    ? store.resetTokens.filter(
        (token): token is ResetTokenRecord =>
          Boolean(
            token &&
              typeof token.jti === "string" &&
              typeof token.userId === "string" &&
              typeof token.expiresAt === "number" &&
              Number.isFinite(token.expiresAt) &&
              token.expiresAt > Date.now(),
          ),
      )
    : [];

  if (!users.some((user) => user.id === "user_demo_1")) {
    users.push(createDemoUser());
  }

  return { users, resetTokens };
}

async function ensureAuthStoreFile(): Promise<void> {
  await mkdir(path.dirname(authStoreFilePath), { recursive: true });

  try {
    await readFile(authStoreFilePath, "utf8");
  } catch {
    await writeFile(authStoreFilePath, JSON.stringify(getDefaultStore(), null, 2), "utf8");
  }
}

async function readStore(): Promise<AuthStoreData> {
  await ensureAuthStoreFile();

  try {
    const raw = await readFile(authStoreFilePath, "utf8");
    return normalizeStore(JSON.parse(raw) as Partial<AuthStoreData>);
  } catch {
    const defaultStore = getDefaultStore();
    await writeFile(authStoreFilePath, JSON.stringify(defaultStore, null, 2), "utf8");
    return defaultStore;
  }
}

async function writeStore(store: AuthStoreData): Promise<void> {
  await writeFile(authStoreFilePath, JSON.stringify(normalizeStore(store), null, 2), "utf8");
}

async function updateStore<T>(updater: (store: AuthStoreData) => T | Promise<T>): Promise<T> {
  const operation = storeWriteQueue.then(async () => {
    const store = await readStore();
    const result = await updater(store);
    await writeStore(store);
    return result;
  });

  storeWriteQueue = operation.then(
    () => undefined,
    () => undefined,
  );

  return operation;
}

export async function findUserByEmail(email: string): Promise<UserRecord | null> {
  const store = await readStore();
  return store.users.find((user) => user.email === email.trim().toLowerCase()) || null;
}

export async function findUserById(userId: string): Promise<UserRecord | null> {
  const store = await readStore();
  return store.users.find((user) => user.id === userId) || null;
}

export async function updateUserPassword(userId: string, passwordHash: string): Promise<boolean> {
  return updateStore((store) => {
    const userIndex = store.users.findIndex((user) => user.id === userId);
    if (userIndex === -1) {
      return false;
    }

    store.users[userIndex] = {
      ...store.users[userIndex],
      passwordHash,
    };

    return true;
  });
}

export async function saveResetToken(jti: string, userId: string, expiresAt: number): Promise<void> {
  await updateStore((store) => {
    store.resetTokens = store.resetTokens.filter((token) => token.jti !== jti);
    store.resetTokens.push({ jti, userId, expiresAt });
  });
}

export async function isResetTokenActive(jti: string, userId: string): Promise<boolean> {
  const store = await readStore();
  const tokenRecord = store.resetTokens.find((token) => token.jti === jti);

  if (!tokenRecord) {
    return false;
  }

  if (tokenRecord.userId !== userId) {
    return false;
  }

  if (Date.now() >= tokenRecord.expiresAt) {
    await updateStore((nextStore) => {
      nextStore.resetTokens = nextStore.resetTokens.filter((token) => token.jti !== jti);
    });
    return false;
  }

  return true;
}

export async function consumeResetToken(jti: string, userId: string): Promise<boolean> {
  return updateStore((store) => {
    const tokenRecord = store.resetTokens.find((token) => token.jti === jti);

    if (!tokenRecord || tokenRecord.userId !== userId) {
      return false;
    }

    if (Date.now() >= tokenRecord.expiresAt) {
      store.resetTokens = store.resetTokens.filter((token) => token.jti !== jti);
      return false;
    }

    store.resetTokens = store.resetTokens.filter((token) => token.jti !== jti);
    return true;
  });
}