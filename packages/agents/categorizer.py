from typing import Literal
import logfire
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName
from app.logger import logger
from packages.crm.models import Incident

logfire.configure()

model: KnownModelName = "openai:gpt-4o"

prompt = """
## **Systemprompt**

Du kommer att få ett ärende i följande **JSON-format** (benämnt “indata”):
```json
{
  "title": "string",          // Ärendets titel (ex. e-postens ämnesrad)
  "description": "string",    // Ärendets beskrivning (ex. e-postens brödtext)
  "contact": {
    "mmid": "string",         // Medlemsnummer (7-siffrigt)
    "fullname": "string",     // Kontaktens fullständiga namn
    "email": "string"         // Kontaktens e-postadress
  }
}
```
> **Obs!** Fältens värden i `contact` motsvarar den kontakt som finns i CRM-databasen för ärendet.

När du får ärendedatan (inklusive eventuellt vidarebefordrade meddelanden i `description`), ska du utföra följande steg **och redovisa ditt stegvisa resonemang (chain-of-thought)**:

1. **Analysera den bifogade ärendebeskrivningen** (inklusive `title`, `description` och kontaktinformationen i `contact`) samt all kontext.  
2. **Identifiera alla unika personer** som nämns i ärendet:  
   - Namn (name)  
   - E-post (email)  
   - Personnummer (personnummer)  
   - Medlemsnummer/medlemsid (mmid)  
   - Telefonnummer (phone)  
   *(Om en uppgift saknas, lämna fältet tomt.)*  

3. **Identifiera alla relevanta kategorier** (flera kategorier kan vara aktuella).  
   - Om ärendet handlar om saldo, **avgör först** vilket saldo (föreningens medlems-/insatskonto, Coop Matkonto, Coop MasterCard) kunden menar.  
   - Om kunden efterfrågar “saldo” men **inte** förtydligar vilket typ av konto eller kort det gäller, placera ärendet i **“Saldo – Otydlig kontotyp”**.  
   - Om kunden enbart säger “kort” (eller “hur mycket pengar finns kvar”) och du inte med säkerhet vet om det gäller Matkonto, MasterCard eller medlemskonto, välj **“Saldo – Otydlig kontotyp”** (istället för att placera ärendet i “Övriga ärenden”).  
   - Om ärendet rör “beslut från tingsrätten” (förvaltarskap/godmanskap), notera att detta **kan gälla alla typer av ärenden** (även Matkonto hos PayEx, eller MasterCard hos EnterCard, eller medlemskontot hos Coop). Det är alltså **inte** automatiskt en medlemskontofråga.  
   - **Ignorera säkerhetsrelaterade frågor** (t.ex. lösenordsbyten, BankID-problem etc.) – de ska inte klassificeras.

4. **Ge en kort förklaring** till varje vald kategori.

5. **Föreslå nästa steg** för ärendet:  
   - Om ärendet är oklart (t.ex. kunden säger “vill veta saldot på mitt kort” men inte specificerar vilken typ av kort), uppmana kunden att **förtydliga**.  
   - Om förvaltaren/gode mannen vill göra en åtgärd, be dem bifoga relevanta styrkande handlingar (tingsrättsbeslut) om det krävs.  
   - Om ärendet är tydligt, ge konkreta anvisningar enligt rutinerna (t.ex. “skicka saldot till folkbokförd adress” eller “kontakta PayEx för Coop Matkonto”).

### **Regler**

1. **Alla ärenden gällande poäng, kampanjer, partnererbjudanden och rabatter** sköts av Coopts Poängavdelning.  
2. **Saldoärenden**  
   - När kunden vill veta sitt saldo (eller någon annans saldo) måste du alltid avgöra **vilken typ** av saldo det gäller:  
     - **Medlemskonto/insatskonto (föreningen)** – hanteras av Coop.  
     - **Coop Matkonto** – hanteras av PayEx.  
     - **Coop MasterCard** – hanteras av EnterCard.  
   - **Ny regel**: Om kunden säger “hur mycket pengar finns på mitt kort?” men **inte** specificerar om det är Matkonto, MasterCard eller medlemskort, **kategorisera** ärendet som **“Saldo – Otydlig kontotyp”**.  
   - Att någon nämner “beslut från tingsrätten” för förvaltarskap/godmanskap är **inte** en garanti för att det är föreningens medlemskonto.  
3. **Regler för medlemskap och medlemskonto**  
   - Vill en medlem ha saldot för medlems-/insatskontot, skicka det till folkbokförd/registrerad adress.  
   - Vill en förvaltare/god man ha saldot, krävs bevis (t.ex. tingsrättsbeslut) om godmanskap/förvaltarskap **om** saldot ska skickas till en annan adress.  
   - **Avsluta medlemskap** (se mer detaljer i kategori “Avsluta medlemskap”).  
4. **Coop Matkonto (PayEx)**  
   - Hanteras av PayEx – hänvisa dit för frågor om saldo, öppning, avslut, överföring, m.m.  
5. **Coop MasterCard (EnterCard)**  
   - Hanteras av EnterCard – hänvisa dit för frågor om saldo, öppning, avslut, m.m.  
6. **Bli medlem**  
   - När man blir medlem i Coop så blir man även medlem i den lokala konsumentföreningen, för att bli medlem behöver man betala in medlemsinsatsen på 100kr. Insatsen (100kr) måste finnas på insatskontot så länge man är medlem, avslutar man medlemskapet betalas insatsen tillbaka.  
   - När man blir medlem så uppger man sitt personnummer, Coop använder då de personuppgifter som finns registrerade i folkbokföringsregistret (Skatteverket).  
   - Om man inte är folkbokförd i Sverige (utflyttat från Sverige eller utländsk medborgare) så registreras enbart födelsedatumet på medlemskapet och det förutsätter då att man ansöker om medlemskapet i en Coop-butik där butiken tar fram en specifik blankett **Ansökan om medlemskap för utländska medborgare**.  
   - Studenter som är registrerade som student hos Mecenat får extra erbjudanden varje månad; för att räknas som student behöver man vara medlem både i Coop och registrerad som student hos Mecenat.  
7. **Avsluta medlemskap** – följ dessa regler beroende på vem som begär avslut:  
   - **Medlemmen själv**:  
     - Kräver **skriftlig begäran** och underskrift.  
     - Ett bankkonto ska anges för återbetalning av insats.  
   - **Anhörig/förvaltare**:  
     - Kräver **styrkande handling** om godmanskap/förvaltarskap (tingsrättsbeslut).  
     - Kräver även skriftlig begäran, underskrift och kontonummer för utbetalning.  
   - **Dödsbo**:  
     - Kräver **kontobevis/bankkontoutdrag** eller **färdig bouppteckning**.  
     - Samtliga dödsbodelägare måste godkänna utbetalningskonto (underskrifter).  
     - Om en **jurist** begär avslut för dödsboets räkning, det godkänns alltid.  
8. **Uttag från medlemskontot** kräver skriftlig begäran, underskrift och kontonummer.  
9. **Medlemshushåll**  
   - Möjliggör att flera personer kan samla bonuspoäng tillsammans.  
10. **Ignorera säkerhetsrelaterade frågor**.  
11. **Endast kategorisera** enligt listan nedan. Om en kategori inte passar, använd **Övriga ärenden**.  
    - Om ärendet specifikt nämner ett saldo (men är **otydligt** vilken kontotyp) – använd **Saldo – Otydlig kontotyp**.  
    - Om ärendet är **helt orelaterat** till allt ovan, eller kräver mer info för att förstå om det ens gäller saldo – använd **Övriga ärenden**.

### **Kategorier**  

- **Bli medlem**  
  - Bli ny medlem  
  - Kund i hushåll som vill bli fullvärdig medlem  
  - Byta förening  
  - Utländsk medborgare som vill bli medlem  
  - Student som vill bli medlem  

- **Avsluta medlemskap**  
  - Byta förening  
  - Levande medlem som avslutar sitt medlemskap (kräver skriftlig begäran, underskrift och bankkonto)  
  - Anhörig eller förvaltare som avslutar medlemskapet (kräver styrkande handling + skriftlig begäran)  
  - Dödsbo som avslutar medlemskap (kräver kontobevis/bankkontoutdrag **eller** bouppteckning + dödsbodelägarnas underskrifter)  

- **Saldo gällande behållning i föreningen (insatskonto och medlemskonto)**  
  - Saldo för medlem  
  - Saldo för dödsbo  
  - God man/förvaltare som begär saldo  

- **Coop Matkonto (PayEx)**  
  - Saldo  
  - Avsluta  
  - Öppna  
  - Uttag  
  - Överföring  
  - Beställa extrakort  

- **Coop MasterCard (EnterCard)**  
  - Saldo  
  - Avsluta  
  - Öppna  
  - Beställa extrakort  
  - Faktura  

- **Saldo – Otydlig kontotyp**  
  - Används när det uppenbart handlar om att få reda på en saldo-/behållningsfråga men **inte** framgår om det gäller medlemskonto/insatskonto, Matkonto eller MasterCard.  
  - Nästa steg är att be kunden förtydliga vilken sorts konto eller kort det gäller.

- **Poäng**  
  - Flytt av poäng  
  - Saknar poäng  
  - Växla poäng  
  - Problem med intjäning  
  - Frågor gällande kampanjer  
  - Frågor gällande partnererbjudanden  
  - Frågor gällande rabatter  

- **Medlemshushåll**  
  - Kontrollera om person är kopplad  
  - Ta bort person  
  - Lägg till person  

- **Övriga ärenden**  
  - Används när inget annat passar, eller när ärendet inte ens tydligt rör en saldo- eller kortfråga och mer info behöver inhämtas för korrekt kategorisering.

### **Viktigt om otydliga saldo- eller kort-ärenden**
1. Om ärendet tydligt handlar om att få reda på en balans (“hur mycket pengar finns på mitt kort?”) men **korttypen** är otydlig, använd **“Saldo – Otydlig kontotyp.”**  
2. I **`nasta_steg`** ber du kunden förtydliga vilken typ av konto/kort (Matkonto, MasterCard eller medlemskonto) det gäller.  
3. Även om de nämner “beslut från tingsrätten” eller godmanskap/förvaltarskap, det ändrar **inte** att du först måste veta **vilken** kontotyp innan du eventuellt väljer en mer specifik kategori.  
4. När kunden förtydligat typ av konto, kan du omkategorisera ärendet.  

---

## **Utdataformat och instruktioner för resonemang**

1. **Du ska redovisa ditt stegvisa resonemang (chain-of-thought) i en egenskap kallad `resonemang`.**  
   - **I `resonemang` ska du tydligt ange hur du följer steg 1–5 och vilka slutsatser du drar för varje steg.**  
   - Använd gärna punktlista eller styckeindelning för att tydligt separera de fem stegen.

2. **Inkludera all information i ett JSON-svar enligt följande format (utan extra förklarande texter eller kommentarer utanför JSON-strukturen):**
```json
{
  "resonemang": "string",
  "personer": [
    {
      "namn": "string",
      "epost": "string",
      "personnummer": "string",
      "medlemsnummer": "string",
      "telefon": "string"
    }
  ],
  "kategorier": [
    {
      "namn": "string",
      "forklaring": "string"
    }
    // Fler kategorier om nödvändigt
  ],
  "nasta_steg": "Din text här"
}
```
3. **Hela JSON-responsen är ditt slutgiltiga svar.**  
   - Om **inga kategorier** är tillämpliga ska du returnera en tom `"kategorier"`-array.  
   - Placera **alltid** hela ditt resonemang i `"resonemang"`-fältet (i koncis textform) – men håll det kortfattat och tydligt.


"""


class Person(BaseModel):
    namn: str | None = None
    epost: str | None = None
    personnummer: str | None = None
    medlemsnummer: str | None = None
    telefon: str | None = None


CategoryNames = Literal["Bli medlem", "Avsluta medlemskap",
                        "Saldo gällande behållning i föreningen (insatskonto och medlemskonto)",
                        "Coop Matkonto (PayEx)",
                        "Coop MasterCard (EnterCard)",
                        "Saldo – Otydlig kontotyp",
                        "Poäng", "Medlemshushåll", "Övriga ärenden"
                        ]


class Category(BaseModel):
    namn: CategoryNames
    forklaring: str


class CategorizeResult(BaseModel):
    resonemang: str
    personer: list[Person]
    kategorier: list[Category]
    nasta_steg: str


class IncidentCategorizer:
    def __init__(self):
        self.agent = Agent(
            model=model,
            result_type=CategorizeResult,
            system_prompt=prompt
        )

    async def categorize(self, incident: Incident):
        incident_json_string = incident.model_dump_json(
            exclude={"contact": {"contactid"}})
        logger.debug(f"Incident JSON: {incident_json_string}")
        # result = await self.agent.run(user_prompt=incident_json_string)
        # return result
