"""
================================================================================
TUGAS PROYEK AKHIR - TEKNIK KOMPILASI
Representasi Tahapan Kompilasi untuk Konstruksi: PERULANGAN (FOR LOOP)
================================================================================

Konstruksi yang disimulasikan:
    for ( init ; condition ; update ) { statements }

Contoh:
    for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }

Program ini mensimulasikan 4 tahapan kompilasi:
    1. Analisis Leksikal  -> memecah source code menjadi token
    2. Analisis Sintaksis  -> membentuk Abstract Syntax Tree (AST)
    3. Analisis Semantik   -> validasi variabel & tipe data sederhana
    4. Generasi Kode Antara -> menghasilkan Three-Address Code (TAC)
================================================================================
"""

import re

# ==============================================================================
# TAHAP 1: ANALISIS LEKSIKAL (LEXICAL ANALYSIS)
# ==============================================================================
# Grammar/Pattern token (didefinisikan dengan Regular Expression):
#
#   KEYWORD    ::= "for"
#   IDENTIFIER ::= [a-zA-Z_][a-zA-Z0-9_]*
#   NUMBER     ::= [0-9]+
#   OPERATOR   ::= "+" | "-" | "*" | "/" | "<" | ">" | "<=" | ">=" | "==" | "="
#   PUNCT      ::= "(" | ")" | "{" | "}" | ";"
#
# BNF pola sintaksis konstruksi yang dipilih:
#
#   <for_stmt>  ::= "for" "(" <init> ";" <condition> ";" <update> ")"
#                    "{" <statements> "}"
#   <init>      ::= <identifier> "=" <value>
#   <condition> ::= <identifier> <rel_op> <value>
#   <update>    ::= <identifier> "=" <identifier> <op> <value>
#   <statements>::= <identifier> "=" <expression>
#   <expression>::= <identifier> <op> <value> | <identifier> | <value>
#   <rel_op>    ::= "<" | ">" | "<=" | ">=" | "=="
#   <op>        ::= "+" | "-" | "*" | "/"
# ==============================================================================

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"<{self.type}:{self.value}>"


# Urutan pengecekan penting: operator 2-karakter dicek lebih dulu (mis. "<=")
TOKEN_SPEC = [
    ("KEYWORD",   r'\bfor\b'),
    ("NUMBER",    r'\d+'),
    ("IDENT",     r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ("REL_OP",    r'<=|>=|==|<|>'),
    ("ASSIGN",    r'='),
    ("OP",        r'[+\-*/]'),
    ("LPAREN",    r'\('),
    ("RPAREN",    r'\)'),
    ("LBRACE",    r'\{'),
    ("RBRACE",    r'\}'),
    ("SEMI",      r';'),
    ("SKIP",      r'[ \t\n]+'),
]

MASTER_REGEX = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC))


def lexical_analysis(source_code):
    """Tahap 1: memecah source code menjadi daftar token."""
    tokens = []
    for match in MASTER_REGEX.finditer(source_code):
        kind = match.lastgroup
        value = match.group()
        if kind == "SKIP":
            continue
        tokens.append(Token(kind, value))
    tokens.append(Token("EOF", None))
    return tokens


# ==============================================================================
# TAHAP 2: ANALISIS SINTAKSIS (SYNTAX ANALYSIS) -> Membentuk AST
# ==============================================================================

class ForNode:
    def __init__(self, init, condition, update, body):
        self.init = init            # AssignNode
        self.condition = condition  # ConditionNode
        self.update = update        # AssignNode
        self.body = body            # list of AssignNode

    def __repr__(self):
        return (f"ForNode(\n  init={self.init},\n  cond={self.condition},\n"
                f"  update={self.update},\n  body={self.body}\n)")


class AssignNode:
    def __init__(self, var, expr):
        self.var = var      # nama variabel (str)
        self.expr = expr    # ExprNode atau nilai literal/identifier (str)

    def __repr__(self):
        return f"Assign({self.var} = {self.expr})"


class ExprNode:
    """Representasi ekspresi biner sederhana: left op right"""
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class ConditionNode:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"Cond({self.left} {self.op} {self.right})"


class Parser:
    """Recursive-descent parser sesuai grammar BNF di atas."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, expected_type):
        tok = self.current()
        if tok.type != expected_type:
            raise SyntaxError(
                f"Sintaksis tidak valid: diharapkan {expected_type}, "
                f"ditemukan {tok.type} ('{tok.value}')"
            )
        self.pos += 1
        return tok

    def parse_for_stmt(self):
        # for ( init ; condition ; update ) { statements }
        self.eat("KEYWORD")     # 'for'
        self.eat("LPAREN")
        init = self.parse_assignment()
        self.eat("SEMI")
        condition = self.parse_condition()
        self.eat("SEMI")
        update = self.parse_assignment()
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = self.parse_statements()
        self.eat("RBRACE")
        return ForNode(init, condition, update, body)

    def parse_assignment(self):
        # <identifier> "=" <expression>
        var = self.eat("IDENT").value
        self.eat("ASSIGN")
        expr = self.parse_expression()
        return AssignNode(var, expr)

    def parse_expression(self):
        # <identifier|number> [ <op> <identifier|number> ]
        left = self.parse_operand()
        if self.current().type == "OP":
            op = self.eat("OP").value
            right = self.parse_operand()
            return ExprNode(left, op, right)
        return left

    def parse_operand(self):
        tok = self.current()
        if tok.type in ("IDENT", "NUMBER"):
            self.pos += 1
            return tok.value
        raise SyntaxError(f"Operand tidak valid: {tok}")

    def parse_condition(self):
        left = self.parse_operand()
        op = self.eat("REL_OP").value
        right = self.parse_operand()
        return ConditionNode(left, op, right)

    def parse_statements(self):
        # bisa lebih dari satu statement dipisah SEMI, di contoh ini 1 statement
        statements = [self.parse_assignment()]
        while self.current().type == "SEMI":
            self.eat("SEMI")
            statements.append(self.parse_assignment())
        return statements


def syntax_analysis(tokens):
    """Tahap 2: membangun AST dari token list."""
    parser = Parser(tokens)
    ast = parser.parse_for_stmt()
    return ast


# ==============================================================================
# TAHAP 3: ANALISIS SEMANTIK (SEMANTIC ANALYSIS)
# ==============================================================================
# Aturan semantik sederhana yang dicek:
#   1. Variabel yang dipakai di condition/update/body harus sudah "dideklarasikan"
#      (di sini: minimal pernah muncul sebagai target assignment sebelumnya,
#       ATAU merupakan variabel loop yang diinisialisasi di 'init').
#   2. Tipe data disederhanakan menjadi satu tipe: "int" (karena hanya angka).
#      Semantic checker memastikan operand berupa NUMBER atau IDENT bertipe int.
# ==============================================================================

class SemanticError(Exception):
    pass


def is_number(token_value):
    return re.fullmatch(r'\d+', token_value) is not None


def semantic_analysis(ast, pre_declared=None):
    """
    Tahap 3: validasi variabel & tipe data. Return symbol table.

    pre_declared: dict variabel yang dianggap sudah dideklarasikan SEBELUM
    loop dieksekusi (mensimulasikan konteks program, mis. 'int sum = 0;'
    yang ditulis sebelum 'for'). Ini realistis karena for-loop biasanya
    tidak berdiri sendiri, melainkan bagian dari program yang lebih besar.
    """
    symbol_table = dict(pre_declared) if pre_declared else {}

    # 1. Variabel dari init otomatis "dideklarasikan" sebagai int
    symbol_table[ast.init.var] = "int"

    def check_operand(operand):
        if is_number(operand):
            return "int"
        else:
            if operand not in symbol_table:
                raise SemanticError(
                    f"Variabel '{operand}' digunakan sebelum dideklarasikan/di-assign."
                )
            return symbol_table[operand]

    # 2. Cek kondisi
    t1 = check_operand(ast.condition.left)
    t2 = check_operand(ast.condition.right)
    if t1 != t2:
        raise SemanticError("Tipe data pada kondisi tidak konsisten.")

    # 3. Cek update
    _check_assignment(ast.update, symbol_table, check_operand)

    # 4. Cek setiap statement di body
    for stmt in ast.body:
        _check_assignment(stmt, symbol_table, check_operand)

    return symbol_table


def _check_assignment(assign_node, symbol_table, check_operand):
    expr = assign_node.expr
    if isinstance(expr, ExprNode):
        t1 = check_operand(expr.left)
        t2 = check_operand(expr.right)
        if t1 != t2:
            raise SemanticError(
                f"Tipe data tidak konsisten pada ekspresi '{expr}'."
            )
        result_type = "int"
    else:
        result_type = check_operand(expr)

    # Variabel target assignment didaftarkan/diupdate ke symbol table
    symbol_table[assign_node.var] = result_type


# ==============================================================================
# TAHAP 4: GENERASI KODE ANTARA (THREE-ADDRESS CODE / TAC)
# ==============================================================================
# Pola terjemahan for-loop ke TAC (mengikuti pola standar kompiler):
#
#   <init>
#   L_start:
#       ifFalse <condition> goto L_end
#       <body statements>
#       <update>
#       goto L_start
#   L_end:
# ==============================================================================

class TACGenerator:
    def __init__(self):
        self.temp_counter = 1
        self.label_counter = 1
        self.code = []

    def new_temp(self):
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def new_label(self):
        l = f"L{self.label_counter}"
        self.label_counter += 1
        return l

    def emit(self, instr):
        self.code.append(instr)

    def gen_expr(self, expr):
        """Menghasilkan TAC untuk ekspresi, return nama variabel/temp hasil."""
        if isinstance(expr, ExprNode):
            temp = self.new_temp()
            self.emit(f"{temp} = {expr.left} {expr.op} {expr.right}")
            return temp
        else:
            return expr  # sudah berupa identifier/angka

    def gen_assign(self, assign_node):
        result = self.gen_expr(assign_node.expr)
        self.emit(f"{assign_node.var} = {result}")

    def generate(self, ast):
        # <init>
        self.gen_assign(ast.init)

        l_start = self.new_label()
        l_end = self.new_label()

        self.emit(f"{l_start}:")

        cond = ast.condition
        self.emit(f"ifFalse ({cond.left} {cond.op} {cond.right}) goto {l_end}")

        # <body>
        for stmt in ast.body:
            self.gen_assign(stmt)

        # <update>
        self.gen_assign(ast.update)

        self.emit(f"goto {l_start}")
        self.emit(f"{l_end}:")

        return self.code


def generate_tac(ast):
    """Tahap 4: menghasilkan Three-Address Code dari AST."""
    generator = TACGenerator()
    return generator.generate(ast)


# ==============================================================================
# DRIVER / PIPELINE UTAMA — menjalankan semua tahapan berurutan
# ==============================================================================

def compile_for_loop(source_code, pre_declared=None, verbose=True):
    if verbose:
        print("=" * 70)
        print(f"SOURCE CODE:\n  {source_code}")
        print("=" * 70)

    # Tahap 1
    tokens = lexical_analysis(source_code)
    if verbose:
        print("\n[TAHAP 1] ANALISIS LEKSIKAL — Token yang dihasilkan:")
        print(" ", tokens)

    # Tahap 2
    ast = syntax_analysis(tokens)
    if verbose:
        print("\n[TAHAP 2] ANALISIS SINTAKSIS — Abstract Syntax Tree (AST):")
        print(ast)

    # Tahap 3
    symbol_table = semantic_analysis(ast, pre_declared=pre_declared)
    if verbose:
        print("\n[TAHAP 3] ANALISIS SEMANTIK — Tabel Simbol (variabel: tipe):")
        for var, typ in symbol_table.items():
            print(f"   {var} : {typ}")
        print("   Status: Semantik VALID (tidak ada error tipe/variabel).")

    # Tahap 4
    tac = generate_tac(ast)
    if verbose:
        print("\n[TAHAP 4] GENERASI KODE ANTARA — Three-Address Code (TAC):")
        for line in tac:
            print(" ", line)
        print("=" * 70)

    return tokens, ast, symbol_table, tac


if __name__ == "__main__":
    # Contoh kasus uji utama:
    #   Konteks program:  int sum = 0;
    #   for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }
    # 'sum' dianggap sudah dideklarasikan sebelum loop (pre_declared),
    # sehingga penggunaannya di dalam body VALID secara semantik.
    source = "for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }"
    compile_for_loop(source, pre_declared={"sum": "int"})

    print("\n\n>>> CONTOH KASUS UJI SEMANTIC ERROR (variabel belum dideklarasikan) <<<\n")
    try:
        # 'total' TIDAK ada di pre_declared, dan tidak pernah di-assign
        # sebelumnya di dalam loop -> harus terdeteksi sebagai error semantik.
        bad_source = "for ( i = 0 ; i < 5 ; i = i + 1 ) { total = total + i }"
        compile_for_loop(bad_source)  # pre_declared kosong -> 'total' tak dikenal
    except SemanticError as e:
        print(f"[SEMANTIC ERROR TERDETEKSI]: {e}")
