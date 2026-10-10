import { Navigate, Route, Routes } from "react-router-dom";

import { RichiedeRuolo } from "./auth";
import { paginaIniziale, useAuth } from "./contesto-auth";
import { Accesso } from "./pages/Accesso";
import { Profilo, RichiedeProfilo } from "./pages/artigiano/profilo/Profilo";
import { Campagna } from "./pages/artigiano/Campagna";
import { DaApprovare } from "./pages/operatore/DaApprovare";
import { VediCampagna } from "./pages/operatore/VediCampagna";

function Ingresso() {
  const { utente } = useAuth();
  if (!utente) return <Navigate to="/accesso" replace />;
  return <Navigate to={paginaIniziale(utente.ruolo)} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/accesso" element={<Accesso />} />
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
      <Route path="/profilo" element={<RichiedeRuolo ruoli={["artigiano"]}>
        <Profilo />
      </RichiedeRuolo>} />
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
      <Route path="/" element={<Ingresso />} />
      <Route path="*" element={<Ingresso />} />
    </Routes>
  );
}
