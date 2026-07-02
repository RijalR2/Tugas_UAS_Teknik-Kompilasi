Tugas Proyek Akhir: Representasi Tahapan Kompilasi

1. Pilihan Konstruksi

Konstruksi yang dipilih: Perulangan (Looping) — bentuk for loop.

Contoh: for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }

Dipilih karena konstruksi for memiliki tiga komponen berbeda (inisialisasi,
kondisi, update) yang sangat representatif untuk didemonstrasikan pada setiap
tahap kompilasi, terutama pada tahap generasi kode karena melibatkan
pembuatan label dan loncatan (jump).


2. Pattern (Pola Sintaks / Grammar)

Pola didefinisikan menggunakan pendekatan Backus-Naur Form (BNF) untuk
struktur, dan Regular Expression untuk token.

2.1 Tata Bahasa BNF

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

2.2 Pola Token (Regular Expression)

Jenis TokenPola RegexContohKEYWORD\bfor\bforNUMBER\d+0, 5, 1IDENT[a-zA-Z_][a-zA-Z0-9_]*i, sumREL_OP<=|>=|==|<|><, <=ASSIGN==OP[+\-*/]+, -LPAREN/RPAREN\( / \)(, )LBRACE/RBRACE\{ / \}{, }SEMI;;


3. Implementasi Program

Program diimplementasikan dalam Python 3 (file: for_loop_compiler.py),
terbagi menjadi 4 tahap yang berurutan seperti pipeline compiler sungguhan.

3.1 Tahap 1 — Analisis Leksikal

Fungsi lexical_analysis() menggunakan satu master regex gabungan untuk
memindai source code dan mengelompokkannya menjadi token bertipe (KEYWORD,
IDENT, NUMBER, REL_OP, dst). Urutan pola regex penting: operator dua
karakter (<=, >=, ==) dicek sebelum operator satu karakter.

Input:

for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }

Output token (disingkat):

<KEYWORD:for> <LPAREN:(> <IDENT:i> <ASSIGN:=> <NUMBER:0> <SEMI:;>
<IDENT:i> <REL_OP:<> <NUMBER:5> <SEMI:;>
<IDENT:i> <ASSIGN:=> <IDENT:i> <OP:+> <NUMBER:1> <RPAREN:)>
<LBRACE:{> <IDENT:sum> <ASSIGN:=> <IDENT:sum> <OP:+> <IDENT:i> <RBRACE:}>

3.2 Tahap 2 — Analisis Sintaksis (Pembentukan AST)

Kelas Parser mengimplementasikan recursive-descent parsing sesuai
grammar BNF. Setiap fungsi (parse_for_stmt, parse_assignment,
parse_condition, parse_expression) merepresentasikan satu aturan produksi
grammar.

ForNode(
  init  = Assign(i = 0)
  cond  = Cond(i < 5)
  update= Assign(i = (i + 1))
  body  = [ Assign(sum = (sum + i)) ]
)

3.3 Tahap 3 — Analisis Semantik

Fungsi semantic_analysis() melakukan dua pengecekan menggunakan tabel
simbol (symbol table):


Keberadaan variabel — setiap variabel yang dipakai harus sudah
"dideklarasikan" (via init, assignment sebelumnya, atau pre_declared).
Konsistensi tipe data — semua nilai disederhanakan sebagai "int".


Kasus valid:

sum : int
i   : int
Status: Semantik VALID

Kasus error (variabel total tidak pernah dideklarasikan):

SemanticError: Variabel 'total' digunakan sebelum dideklarasikan/di-assign.

3.4 Tahap 4 — Generasi Kode Antara (Three-Address Code)

Kelas TACGenerator menerjemahkan AST menjadi TAC menggunakan pola
goto/label standar untuk loop.

Output TAC untuk kasus uji:

i = 0
L1:
ifFalse (i < 5) goto L2
t1 = sum + i
sum = t1
t2 = i + 1
i = t2
goto L1
L2:


4. Cara Menjalankan Program

bashpython3 for_loop_compiler.py

Program akan otomatis menjalankan kasus uji valid dan kasus uji error
semantik, lalu mencetak hasil dari keempat tahap kompilasi secara berurutan.


5. Kesimpulan

Program ini berhasil mensimulasikan alur kompilasi lengkap untuk konstruksi
for loop: Leksikal → Sintaksis → Semantik → Generasi Kode
(TAC), menunjukkan bagaimana compiler sungguhan memproses kode sumber
secara bertahap hingga siap diterjemahkan ke kode target.
