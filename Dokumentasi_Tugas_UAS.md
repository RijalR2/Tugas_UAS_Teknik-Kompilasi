# Tugas Proyek Akhir — Representasi Tahapan Kompilasi
## Konstruksi: Perulangan (`for` loop)

---

## 1. Pilihan Konstruksi

Konstruksi sintaksis yang dipilih adalah **perulangan `for`**, dengan bentuk umum:

```
for ( init ; condition ; update ) { statements }
```

Contoh konkret yang digunakan sebagai kasus uji:

```
for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }
```

Konstruksi ini dipilih karena memuat tiga komponen sintaksis berbeda dalam satu
statement (inisialisasi, kondisi, update) sehingga cukup representatif untuk
mendemonstrasikan seluruh tahapan kompilasi.

---

## 2. Pattern (Pola Sintaksis)

Pola tata bahasa didefinisikan dalam dua bentuk: **BNF** (untuk struktur) dan
**Regular Expression** (untuk token).

### 2.1 Tata Bahasa BNF

```
<for_stmt>   ::= "for" "(" <init> ";" <condition> ";" <update> ")"
                  "{" <statements> "}"
<init>       ::= <identifier> "=" <value>
<condition>  ::= <identifier> <rel_op> <value>
<update>     ::= <identifier> "=" <identifier> <op> <value>
<statements> ::= <identifier> "=" <expression>
<expression> ::= <identifier> <op> <value> | <identifier> | <value>
<rel_op>     ::= "<" | ">" | "<=" | ">=" | "=="
<op>         ::= "+" | "-" | "*" | "/"
<identifier> ::= [a-zA-Z_][a-zA-Z0-9_]*
<value>      ::= <identifier> | <number>
```

### 2.2 Pola Token (Regular Expression)

| Jenis Token | Pola Regex                     | Contoh          |
|-------------|---------------------------------|-----------------|
| KEYWORD     | `\bfor\b`                       | `for`           |
| NUMBER      | `\d+`                           | `0`, `5`, `1`   |
| IDENT       | `[a-zA-Z_][a-zA-Z0-9_]*`        | `i`, `sum`      |
| REL_OP      | `<=\|>=\|==\|<\|>`               | `<`, `<=`       |
| ASSIGN      | `=`                              | `=`             |
| OP          | `[+\-*/]`                       | `+`, `-`        |
| LPAREN/RPAREN | `\(` / `\)`                    | `(`, `)`        |
| LBRACE/RBRACE | `\{` / `\}`                    | `{`, `}`        |
| SEMI        | `;`                              | `;`             |

---

## 3. Implementasi Program

Program diimplementasikan dalam **Python 3** (file: `for_loop_compiler.py`),
terbagi menjadi 4 tahap yang berurutan seperti pipeline compiler sungguhan.

### 3.1 Tahap 1 — Analisis Leksikal

Fungsi `lexical_analysis()` menggunakan satu *master regex* gabungan (teknik
umum untuk lexer sederhana) untuk memindai source code karakter demi karakter
dan mengelompokkannya menjadi token bertipe (`KEYWORD`, `IDENT`, `NUMBER`,
`REL_OP`, dst). Urutan pola regex penting: operator dua karakter (`<=`, `>=`,
`==`) harus dicek **sebelum** operator satu karakter agar tidak salah kenali.

**Input:**
```
for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }
```

**Output token (disingkat):**
```
<KEYWORD:for> <LPAREN:(> <IDENT:i> <ASSIGN:=> <NUMBER:0> <SEMI:;>
<IDENT:i> <REL_OP:<> <NUMBER:5> <SEMI:;>
<IDENT:i> <ASSIGN:=> <IDENT:i> <OP:+> <NUMBER:1> <RPAREN:)>
<LBRACE:{> <IDENT:sum> <ASSIGN:=> <IDENT:sum> <OP:+> <IDENT:i> <RBRACE:}>
```

### 3.2 Tahap 2 — Analisis Sintaksis (Pembentukan AST)

Kelas `Parser` mengimplementasikan **recursive-descent parsing** sesuai
grammar BNF di atas. Setiap fungsi (`parse_for_stmt`, `parse_assignment`,
`parse_condition`, `parse_expression`) merepresentasikan satu aturan produksi
grammar, dan setiap kali aturan cocok, sebuah *node* AST dibentuk.

Struktur AST yang dihasilkan (bentuk pohon disederhanakan menjadi teks):

```
ForNode(
  init  = Assign(i = 0)
  cond  = Cond(i < 5)
  update= Assign(i = (i + 1))
  body  = [ Assign(sum = (sum + i)) ]
)
```

Jika token tidak sesuai urutan yang diharapkan grammar (misalnya kurung tidak
seimbang), fungsi `eat()` akan melempar `SyntaxError`.

### 3.3 Tahap 3 — Analisis Semantik

Fungsi `semantic_analysis()` melakukan dua pengecekan dasar menggunakan
**tabel simbol** (symbol table):

1. **Keberadaan variabel** — setiap variabel yang dipakai (di kondisi, update,
   atau body) harus sudah "dideklarasikan", baik melalui `init` loop, melalui
   assignment sebelumnya, maupun melalui parameter `pre_declared` yang
   mensimulasikan variabel yang dideklarasikan **di luar** loop (misalnya
   `int sum = 0;` sebelum `for`).
2. **Konsistensi tipe data** — karena semua nilai berupa bilangan bulat,
   tipe disederhanakan menjadi `"int"`; program memastikan kedua operand pada
   sebuah ekspresi memiliki tipe yang sama.

**Kasus valid** (dengan `pre_declared={"sum": "int"}`):
```
sum : int
i   : int
Status: Semantik VALID
```

**Kasus error** (variabel `total` dipakai tapi tidak pernah dideklarasikan):
```
SemanticError: Variabel 'total' digunakan sebelum dideklarasikan/di-assign.
```

Ini membuktikan bahwa tahap semantik berhasil mendeteksi kesalahan yang
**tidak** bisa ditangkap oleh lexer maupun parser (karena secara sintaksis,
`total = total + i` tetap valid).

### 3.4 Tahap 4 — Generasi Kode Antara (Three-Address Code)

Kelas `TACGenerator` menerjemahkan AST menjadi TAC menggunakan pola
standar penerjemahan `for` menjadi struktur `goto`/label (mirip cara compiler
sungguhan menerjemahkan loop ke kode beralamat tiga):

```
<init>
L_start:
    ifFalse <condition> goto L_end
    <body statements>
    <update>
    goto L_start
L_end:
```

Setiap ekspresi biner (mis. `sum + i`) dipecah menjadi **variabel sementara**
(`t1`, `t2`, ...) agar setiap instruksi TAC hanya memuat maksimal satu operator
— inilah ciri khas *three-address code*.

**Output TAC untuk kasus uji:**
```
i = 0
L1:
ifFalse (i < 5) goto L2
t1 = sum + i
sum = t1
t2 = i + 1
i = t2
goto L1
L2:
```

Penjelasan tiap baris:
| Baris TAC | Makna |
|---|---|
| `i = 0` | Inisialisasi variabel loop |
| `L1:` | Label awal iterasi (tempat kembali setiap putaran) |
| `ifFalse (i < 5) goto L2` | Jika kondisi salah, lompat keluar loop |
| `t1 = sum + i` | Hitung `sum + i` ke variabel sementara `t1` |
| `sum = t1` | Simpan hasil ke variabel `sum` |
| `t2 = i + 1` | Hitung `i + 1` (bagian update) |
| `i = t2` | Simpan hasil update ke `i` |
| `goto L1` | Kembali ke awal loop |
| `L2:` | Label akhir loop |

---

## 4. Cara Menjalankan Program

```bash
python3 for_loop_compiler.py
```

Program akan otomatis menjalankan:
1. Kasus uji valid: `for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }`
2. Kasus uji error semantik: menggunakan variabel `total` yang tidak dideklarasikan

dan mencetak hasil dari keempat tahap kompilasi ke layar secara berurutan.

---

## 5. Kesimpulan

Program ini berhasil mensimulasikan alur kompilasi lengkap untuk konstruksi
`for` loop:

- **Leksikal** mengubah teks mentah menjadi token terstruktur.
- **Sintaksis** memverifikasi urutan token sesuai grammar dan membentuk AST.
- **Semantik** memvalidasi makna program (variabel & tipe) yang tidak bisa
  dideteksi oleh parser saja.
- **Generasi Kode (TAC)** menerjemahkan AST menjadi instruksi beralamat tiga
  yang merupakan representasi *intermediate* sebelum kode mesin/assembly
  dihasilkan.

Keempat tahap ini menunjukkan bagaimana compiler sungguhan memproses kode
sumber secara bertahap, dari representasi teks murni hingga representasi
yang siap dioptimasi dan diterjemahkan lebih lanjut ke kode target.
