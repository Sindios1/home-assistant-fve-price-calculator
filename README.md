# FVE SPOT Revenue CZ (Kalkulačka pro Home Assistant)

Tato integrace pro Home Assistant slouží ke spolehlivému a přesnému **výpočtu skutečných výnosů z prodeje elektřiny do sítě** na základě dynamických (SPOTových) nebo fixních cen. Oproti klasickému Energy Dashboardu dokáže chytrým způsobem rozpočítávat denní i měsíční poplatky poskytovateli.

---

## 📥 Instalace

Nejrychlejší způsob, jak repozitář do vašeho Home Assistant přidat přes **HACS**, je kliknout na tlačítko níže:

[![Přidat do HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sindios1&repository=home-assistant-fve-price-calculator&category=integration)

<details>
<summary><b>Nebo manuálně přes HACS:</b></summary>
<br>

1. Otevřete **HACS** ve vašem Home Assistantu.
2. V pravém horním rohu klikněte na 3 tečky a vyberte **Vlastní repozitáře (Custom repositories)**.
3. Do pole `Repozitář` zkopírujte odkaz na tento váš GitHub repozitář (`https://github.com/Sindios1/home-assistant-fve-price-calculator`).
4. Do pole `Kategorie` vyberte **Integrace**.
5. Klikněte na **Přidat**. Následně integraci stáhněte.

</details>

*Nezapomeňte po instalaci Home Assistant restartovat (Nastavení -> Systém -> Tlačítko restartu).*

---

## ⚙️ Spuštění a nastavení

Až Home Assistant naběhne, jděte do **Nastavení** 👉 **Zařízení a služby** 👉 Klikněte vpravo dole na modré tlačítko **+ Přidat integraci**.
Do vyhledávání napište `FVE` a měla by na vás vyskočit integrace **Nastavení FVE výnosů (SPOT)**. 

Během jednokrokového nastavování uvidíte následující parametry:

> [!WARNING]
> **1. Senzor exportované energie (v kWh)**
> **Zde většina lidí chybuje!** Musíte vybrat senzor, který ukazuje **kumulativní energii (v kWh)**. 
> - ✅ **Správně:** Senzor typu `Denní přetak do sítě (Daily Export)` nebo `Celkový historický přetok (Lifetime Export)`. Integrace detekuje každý nárůst čísla a hned jej promítne do vydělaných peněz. Když se denní senzor o půlnoci vynuluje, integrace pád ignoruje a nic neodepíše.
> - ❌ **Špatně:** Senzor typu `Okamžitý výkon do sítě ve Wattech (W/kW)`. Tento senzor integrace nebere!

> [!TIP]
> **2. Senzor SPOT ceny (v kWh)**
> Doporučujeme používat samostatnou integraci např. **[Czech Energy Spot Prices](https://github.com/rnovacek/homeassistant_cz_energy_spot_prices)**. Z té zde zkopírujte její senzor s aktuální hodinovou cenou (musí být převeden na cenu za 1 kWh, nikoliv MWh). 

> [!NOTE]
> **3. Poplatky zprostředkovateli**
> - **Poplatek za každou prodanou MWh:** Zde zadejte částku v Kč, kterou si váš výkupce strhává z každé prodané megawatthodiny (tzv. marže). Integrace si částku pro výpočet sama interně dělí číslem 1000.
> - **Měsíční poplatek provozovateli:** Fixní částka v Kč, kterou každý měsíc platíte jako paušál. Je tu obrovská výhoda: Integrace tento poplatek pod pokličkou vezme, vydělí ho počtem dnů v aktuálním měsíci a **tuto drobnou poměrnou částku vám pak strhává ze zisku rovnoměrně každý den přesně o půlnoci**.

---

## 📊 Výsledek

Okamžitě po uložení se vám do systému vygenerují 4 čistě nové senzory:

* 💰 **Denní výnos FVE** (Každý den o půlnoci odepíše poměrný denní poplatek, čímž spadne jemně do mínusu a celý den pak výnosy roste)
* 💰 **Týdenní výnos FVE** (Resetuje se vždy v pondělí o půlnoci)
* 💰 **Měsíční výnos FVE** (Resetuje se vždy 1. den v měsíci)
* 💰 **Roční výnos FVE** (Resetuje se na Nový rok)

S těmito senzory si můžete následně postavit krásný sloupečkový graf přesně nad těmito čtyřmi metrikami! Všechna data se zapisují do paměti a **přežijí klasický restart** celého systému.
