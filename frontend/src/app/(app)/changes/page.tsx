"use client";
import { Suspense } from "react";
import { ChangesPage } from "@/components/patches/ChangesPage";
import { RequireProject } from "@/components/shell/RequireProject";

export default function Page() {
  return <Suspense fallback={null}><RequireProject>{(id) => <ChangesPage repoId={id} />}</RequireProject></Suspense>;
}
