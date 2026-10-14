/** Creazioni di prova: si ricordano le sole email, mai le password. */
import { ApiErrore } from "../http";
import type { ArtigianoCreato, NuovoArtigiano } from "../artigiani";

const emailUsate = new Set([
  "mario@falegnameriabianchi.it",
  "laura@consorzio.example",
  "admin@consorzio.example",
]);
let prossimoId = 100;

export async function creaArtigianoEsempio(
  dati: NuovoArtigiano,
): Promise<ArtigianoCreato> {
  const email = dati.email.trim().toLowerCase();
  const nome = dati.nome.trim();
  if (!nome || !/^\S+@\S+\.\S+$/.test(email) || email.length > 320)
    throw new ApiErrore(422, "Compilare email e nome con dati validi.");
  if (emailUsate.has(email)) throw new ApiErrore(409, "Email già registrata.");
  emailUsate.add(email);
  const casuali = crypto.getRandomValues(new Uint8Array(18));
  const password_provvisoria = btoa(String.fromCharCode(...casuali))
    .replaceAll("+", "-")
    .replaceAll("/", "_");
  return { id: prossimoId++, email, nome, password_provvisoria };
}
