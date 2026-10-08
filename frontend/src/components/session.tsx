import { createContext, useContext } from "react";
import { User } from "../api";

export const SessionContext = createContext<{ user: User; signOut: () => void } | null>(null);

export function useSession() {
  const s = useContext(SessionContext);
  if (!s) throw new Error("useSession outside SessionContext");
  return s;
}
