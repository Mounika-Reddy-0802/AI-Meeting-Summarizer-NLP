import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

export default function Home() {
  const { token, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready) void router.replace(token ? "/dashboard" : "/login");
  }, [ready, token, router]);

  return null;
}
