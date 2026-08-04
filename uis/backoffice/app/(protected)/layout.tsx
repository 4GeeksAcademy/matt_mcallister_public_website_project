import { PropsWithChildren } from "react";

import ProtectedShell from "@/components/ProtectedShell";

export default function ProtectedLayout({ children }: PropsWithChildren) {
  return <ProtectedShell>{children}</ProtectedShell>;
}
