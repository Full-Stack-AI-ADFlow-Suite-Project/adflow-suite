import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { RichiedeRuolo } from "./auth";
import { paginaIniziale, useAuth } from "./contesto-auth";
import { Accesso } from "./pages/Accesso";
import { Calendario } from "./pages/Calendario";
import { Profilo, RichiedeProfilo } from "./pages/artigiano/profilo/Profilo";
import { Archivio } from "./pages/artigiano/Archivio";
import { Campagna } from "./pages/artigiano/Campagna";
import { Campagne } from "./pages/artigiano/Campagne";
import { Ingresso } from "./pages/artigiano/Ingresso";
import { ArchivioArtigiano } from "./pages/operatore/ArchivioArtigiano";
import { Artigiani } from "./pages/operatore/Artigiani";
import { Artigiano } from "./pages/operatore/Artigiano";
import { CampagneArtigiano } from "./pages/operatore/CampagneArtigiano";
import { DaApprovare } from "./pages/operatore/DaApprovare";
import { NuovoArtigiano } from "./pages/operatore/NuovoArtigiano";
import { VediCampagna } from "./pages/operatore/VediCampagna";

/** Porta alla pagina di partenza del ruolo (spec R-29). */
function Partenza() {
  const { utente } = useAuth();
  if (!utente) return <Navigate to="/accesso" replace />;
  return <Navigate to={paginaIniziale(utente.ruolo)} replace />;
}

/** Il profilo serve solo all'artigiano: operatore e admin passano (spec R-29). */
function ConProfiloSeArtigiano({ children }: { children: ReactNode }) {
  const { utente } = useAuth();
  return utente?.ruolo === "artigiano" ? (
    <RichiedeProfilo>{children}</RichiedeProfilo>
  ) : (
    children
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/accesso" element={<Accesso />} />
      <Route
        path="/ingresso"
        element={
          <RichiedeRuolo ruoli={["artigiano"]}>
            <RichiedeProfilo>
              <Ingresso />
            </RichiedeProfilo>
          </RichiedeRuolo>
        }
      />
      <Route
        path="/campagne"
        element={
          <RichiedeRuolo ruoli={["artigiano"]}>
            <RichiedeProfilo>
              <Campagne />
            </RichiedeProfilo>
          </RichiedeRuolo>
        }
      />
      <Route
        path="/calendario"
        element={
          <RichiedeRuolo ruoli={["artigiano", "operatore", "admin"]}>
            <ConProfiloSeArtigiano>
              <Calendario />
            </ConProfiloSeArtigiano>
          </RichiedeRuolo>
        }
      />
      <Route
        path="/archivio"
        element={
          <RichiedeRuolo ruoli={["artigiano"]}>
            <RichiedeProfilo>
              <Archivio />
            </RichiedeProfilo>
          </RichiedeRuolo>
        }
      />
      <Route
        path="/campagna"
        element={
          <RichiedeRuolo ruoli={["artigiano"]}>
            <RichiedeProfilo>
              <Campagna />
            </RichiedeProfilo>
          </RichiedeRuolo>
        }
      />
      <Route
        path="/profilo"
        element={
          <RichiedeRuolo ruoli={["artigiano"]}>
            <Profilo />
          </RichiedeRuolo>
        }
      />
      <Route
        path="/da-approvare"
        element={
          <RichiedeRuolo ruoli={["operatore", "admin"]}>
            <DaApprovare />
          </RichiedeRuolo>
        }
      />
      <Route
        path="/campagne/:id"
        element={
          <RichiedeRuolo ruoli={["operatore", "admin"]}>
            <VediCampagna />
          </RichiedeRuolo>
        }
      />
      <Route
        path="/artigiani"
        element={
          <RichiedeRuolo ruoli={["operatore", "admin"]}>
            <Artigiani />
          </RichiedeRuolo>
        }
      />
      <Route
        path="/artigiani/:id"
        element={
          <RichiedeRuolo ruoli={["operatore", "admin"]}>
            <Artigiano />
          </RichiedeRuolo>
        }
      />
      <Route
        path="/artigiani/:id/campagne"
        element={
          <RichiedeRuolo ruoli={["operatore", "admin"]}>
            <CampagneArtigiano />
          </RichiedeRuolo>
        }
      />
      <Route
        path="/artigiani/:id/archivio"
        element={
          <RichiedeRuolo ruoli={["operatore", "admin"]}>
            <ArchivioArtigiano />
          </RichiedeRuolo>
        }
      />
      <Route
        path="/nuovo-artigiano"
        element={
          <RichiedeRuolo ruoli={["operatore", "admin"]}>
            <NuovoArtigiano />
          </RichiedeRuolo>
        }
      />
      <Route path="/" element={<Partenza />} />
      <Route path="*" element={<Partenza />} />
    </Routes>
  );
}
