# snap-cam

## Versionierung (german)

**snap-cam** benutzt __Semantische Versionierung__, d.h. jede Versionsangabe
folgt dem Schema
_X_._Y_._Z_[._R_._C_] (_major_._minor_._patchLevel_[._release_._counter_]).
_X_, _Y_, _Z_, _R_, _C_ sind alle samt ganze Zahlen, die - abhängig von
erfolgten Änderungen - immer bei jeder neuen Version **um 1 erhöht**
oder **auf 0 zurückgesetzt** werden. Aufgrund dessen sollte jeder relativ gut
abschätzen können, wie alt bzw. wie weit weg eine fragliche Installation von
der aktuellen Version ist. [._R_._C_] bedeutet, dass dieser Teil optional ist.
Falls selbiger nicht vorhanden ist, wird er intern mit `0.0` ersetzt.
Im Prinzip kann jedes `.0` Suffix weggelassen werden, aber aus Gründen der
besseren Lesbarkeit wird dies nicht für die ersten drei Zahlen empfohlen.

_X_, _Y_, _Z_, _R_, _C_ haben insbesondere folgende Bedeutung:
* _X_ (**major**): gemachte Änderungen sind inkompatibel zu jeder vorherigen
	Version.
* _Y_ (**minor**): sichtbare Feature/Schnittstellen-Änderungen oder mehr oder
	weniger große Änderungen bzgl. Implementierung wurden vorgenommen. Jedoch
	ist die Abwärtskompatibilität zu jeder vorherigen Version mit der
	gleichen major Zahl (_X_) erhalten geblieben.
* _Z_ (**patchLevel**): minimale Code-Änderungen wurden vorgenommen, um einen
	Fehler alias Bug zu beheben oder neues Gerät zu unterstützen.
* _R_ (**release**): wird genutzt, um den Typ der Version zu beschreiben:
	* **0**: stabile, offizielle und somit für einen bestimmten Zeitraum
		unterstützte Version.
	* **1**: alpha, experimentell - nicht unterstützt. In dieser Phase können
		vollkommen neue Feature, Implementierungen, Nutzerschnittstellen,
		Frameworks, Technologien eingeführt bzw. ausgetauscht werden. Jeder der
		solch eine Version installiert, muss damit rechnen, dass gewisse Dinge
		nicht oder nicht wie erwartet funktionieren, fehlerhaft oder nur
		prototypisch implementiert sind, und somit noch viele scharfe Kanten,
		die durch aus wehtun oder sogar Geräte beschädigen/unbrauchbar machen
		können.
	* **2**: beta, testing: I.d.R. impliziert eine solche Version, dass keine
		neuen Features, Implementierungen, Nutzerschnittstellen,
		Technologie-Umstellungen, etc. mehr in die Software aufgenommen werden.
		Der Fokus liegt hier auf der Stabilisierung aller vorgenommenen
		Änderungen und die Software an freiwillige Tester zwecks feedback zu
		verteilen.
	* **3**: reserviert: Diese Ziffer kann für Vorab- oder sogenannte
		"Early-Access"-Versionen oder ähnliches verwendet werden. Da aber
		"finale" Betas normalerweise schon die Qualität eines Vorab-Version
		haben, wird diese Ziffer nur sehr selten, wenn überhaupt, zum Einsatz
		kommen.
	* **4**: head: kann dazu genutzt werden, um zu signalisieren, dass diese
		Version direkt auf den Quellen im HEAD (Kopf) des aktuellen
		Entwicklungszweigs beruht und mit voller Absicht jede stabile, alpha
		oder installierte Beta-Version mit gleichem Präfix "überschreibt".
		Beispielsweise könnten sogenannte "nightly builds" des
		Hauptentwicklungszweigs diese Ziffer nutzen.
	* **5-9**: reserviert für mögliche zukünftige Nutzung.
* _C_ (**counter**): Das noch fehlende "Bit", um dies als _neue_ bzw.
	Folge-Version kenntlich zu machen.

**ACHTUNG:** Je nach Komplexität des Projekts oder vorgenommenen Änderungen
kann es sein, dass man nie eine mit '._R_._C_' versehene Version sieht. So kann
z.B. nach einer relativ triviale Fehlerbeseitigungen/bug fix sofort _Z_ erhöht
werden, ohne erst die alpha, beta oder Vorab-Versions-Phase zu durchlaufen.
Wenn eine Zahl erhöht wird, werden logischer Weise alle im Versionsstring
folgenden Zahlen auf `0` zurückgesetzt.

Es ist erlaubt, weitere Zahlen dem Versionsstring hinzuzufügen. Es wird jedoch
empfohlen, selbiges immer mit 2er-Paaren zu tun: z.B. die erste nutzen, um den
Typ oder die entsprechende Entwicklungsphase zu verewigen und die zweite als
einfachen Zähler verwenden.

**ACHTUNG:** Im Versionsstring dürfen **nur** Zahlen und Punkte auftauchen.
D.h. dass auch nutzlose Suffixe wie '-rc\*' oder ähnliches verboten sind.


## Versioning (englisch)

**snap-cam** uses __semantic versioning__, i.e. each release is numbered
_X_._Y_._Z_[._R_._C_] (_major_._minor_._patchLevel_[._release_._counter_]).
_X_, _Y_, _Z_, _R_, _C_ are all
integers, which get - depending on the changes made - **increased by 1** or
**reset to 0** for any new version. This way anybody should be able to make a
good guess, how far behind the installation in question is. [._R_._C_] means,
this part is optional.  If it is missing, it gets internally replaced by
`.0.0`. Actually any trailing `.0` can be omitted, but for better readability
this is not recommended for the first three numbers.

Especially the _X_, _Y_, _Z_, _R_, _C_ numbers have the following meaning:
* _X_ (**major**): changes were made, which are incompatible to any previous
	version.
* _Y_ (**minor**): visible feature/interface changes or more or less  major
	changes of internal implementation details, but retains backward
	compatibility to any previous version with the same major number (_X_).
* _Z_ (**patchLevel**): gets usually changed, when minor code changes have been
	made to fix a certain issues, e.g. support for a [new] device or misc. bugs.
* _R_ (**release**): used to describe the type of the release:
	* **0**: stable, official release and thus supported for a certain period.
	* **1**: alpha, experimental - unsupported. At this stage new features
		might be introduced, implementations can be changed completely, UI
		frameworks or technology use, etc. may change. Everyone, who installs
		such a version should expect that some stuff might be broken, has rough
		edges and may damage other things!
	* **2**: beta, testing: Usually this implies a feature, implementation, UI,
		technology freeze. The focus is to stabilize all changes being made and
		hand out the new packages to users willingly to test it.
	* **3**: reserved: this digit might be used for pre-releases or so called
		early-access versions or something similar. However, since "final" beta
		versions have usually the quality of a pre-release, this digit will be
		used very seldom, if at all.
	* **4**: head: might be used to indicate, that this version was build from
		the head of the development branch, and intentionally "overwrites" any
		stable, alpha, or beta release having the same prefix. E.g. nightly
		builds of the master branch may use this digit.
	* **5-9**: reserved for future use.
* _C_ (**counter**): Just the missing "bit" to be able to overwrite the
	previous version and just denotes an incremental build.

**NOTE:** Depending on the complexity of the project or changes you might never
see an '._R_._C_' tagged version. E.g. for a very simple bug fix, _Z_ might get
incremented immediately without going through any alpha, beta or pre-release
phase. If a number gets incremented, all trailing numbers get of course reset
to `0`.

One may add any other _.number_ to the version string, however it is
recommended to do that in pairs, i.e. the first one marks a certain type or
stage and the second one simply gets incremented on demand.

**NOTE** that **only** numbers and dots are allowed within a version string!
So useless suffixes like '-rc\*' or the like are prohibited.
