"use client";
import { Suspense } from "react";
import { ExplorerPage } from "@/components/explorer/ExplorerPage";
import { RequireProject } from "@/components/shell/RequireProject";

export default function Page() {
  return <Suspense fallback={null}><RequireProject>{(id) => <ExplorerPage repoId={id} />}</RequireProject></Suspense>;
}
