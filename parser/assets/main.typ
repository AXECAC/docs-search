#import "conf.typ": conf, intro, conclusion
#show: conf.with(
  title: [Вариант 18],
  type: "referat",
  info: (
    author: (
      name: [Смирнова Егора Ильича],
      faculty: [КНиИТ],
      group: "351",
      sex: "male",
    ),
    inspector: (
      degree: "",
      name: "",
    ),
  ),
  settings: (
    title_page: (
      enabled: true,
    ),
    contents_page: (
      enabled: true,
    ),
  ),
)

= КР
Имеются следующие данные о величине товарооборота для 50 магазинов города
($Delta_i$ ---товарооборот, усл. руб.; $n_i$ --- число магазинов)
#align(center, [
  #table(
    columns: 7,
    $Delta_i$, $[0, 50)$, $[50, 100)$, $[100, 150)$, $[150, 200)$, $[200, 250)$, $[250, 300)$,

    $n_i$, $15$, $12$, $9$, $7$, $4$, $3$
  )
])

== Построить гистограмму и полигон частот
Гистограмма:
#image("images/01.png")

#align(center, [
  #table(
    columns: 7,
    $x_i$, $25$, $75$, $125$, $175$, $225$, $275$
  )
])

Полигон:
#image("images/02.png")

== Записать эмпирическую функцию распределения и построить её график

$
  limits(F_n)^~ = cases(
    0\, quad quad quad quad quad x lt.eq 25,
    15 / 50\, quad quad 25 < x lt.eq 75,
    27 / 50\, quad quad 75 < x lt.eq 125,
    36 / 50\, quad space 125 < x lt.eq 175,
    43 / 50\, quad space 175 < x lt.eq 225,
    47 / 50\, quad space 225 < x lt.eq 275,
    1\, quad quad quad quad space space x > 275
  ) = cases(
    0 \, quad quad quad quad quad x lt.eq 25,
    0.3 \, quad quad 25 < x lt.eq 75,
    0.54 \, quad space space 75 < x lt.eq 125,
    0.72 \, quad 125 < x lt.eq 175,
    0.86 \, quad 175 < x lt.eq 225,
    0.94 \, quad 225 < x lt.eq 275,
    1\, quad quad quad quad quad x > 275
  )
$

#image("images/03.png")

== Определить числовые характеристики вариационного ряда: $overline(x), S^2, S, accent(sigma, ~)^2, accent(sigma, ~)$

Выборочное среднее:
$
  overline(x) = 1 / 50
    dot ( 25 dot 15
        + 75 dot 12
        + 125 dot 9
        + 175 dot 7
        + 225 dot 4
        + 275 dot 3 ) = 107
$

Выборочная дисперсия (смещенная оценка дисперсии):
$
  S^2 = 1 / 50
    dot ( 25^2 dot 15
        + 75^2 dot 12
        + 125^2 dot 9
        + 175^2 dot 7
        + 225^2 dot 4
        + 275^2 dot 3 ) - \
    - 107 = 17118
$

Выборочная дисперсия (несмещенная оценка дисперсии):
$
  accent(sigma, ~)^2 = 50 / 49 dot 17118 = 17467.35
$

Выборочное среднее квадратичное отклонение (смещенное)
$
  S = 130.84
$

Выборочное среднее квадратичное отклонение (несмещенное)
$
   accent(sigma, ~) = 132.16
$

== Предполагая нормальным распределение генеральной совокупности, построить доверительные интервалы надежности $0.95$ и $0.99$ для параметров нормального распределения.
Интервал имеет вид $overline(x) - t_gamma sigma / sqrt(n) < a < overline(x)
+ t_gamma sigma / sqrt(n)$. Имеем $sqrt(n) = sqrt(50) approx 7.07$.

Тогда при $gamma = 0.95; space t_gamma = 2.083$

$
  [107 - (2.083 dot 132.16) / 7.07; 107 + (2.083 dot 132.16) / 7.07]
    = [68.06; 145.94]
$

Тогда при $gamma = 0.99; space t_gamma = 2.708$

$
  [107 - (2.708 dot 132.16) / 7.07; 107 + (2.708 dot 132.16) / 7.07]
    = [56.38; 157.62]
$

== Критериями Пирсона и Колмогорова при уровне значимости $0.05$ проверить гипотезу о нормальном распределении наблюдаемой случайной величины.
#align(center, [
  #table(
    columns: 4,
    table.header(
      table.cell(rowspan: 2, stroke: (
        bottom: 0pt,
      ))[*Номер\ интервала $i$*],
      table.cell(colspan: 2, rowspan: 2)[*Граница\ интервала*],
      table.cell(rowspan: 2, stroke: (
        bottom: 0pt,
      ))[*Частота\ $n_i$*],
      [],
      [$x_i$], [$x_(i+1)$], [],
    ),

    $1$, $25 $, $75 $, $15$,
    $2$, $75 $, $125$, $12$,
    $3$, $125$, $175$, $9 $,
    $4$, $175$, $225$, $7 $,
    $5$, $225$, $300$, $4 $,
  )
])

$
  x_i^\* = (x_i + x_(i + 1)) / 2
$

#align(center,[
  #table(
    columns: 6,
    $x_i^\*$, $50$, $100$, $150$, $200$, $250$,
    $n_i$, $15$, $12$, $9$, $7$, $4$,
  )
])

$
  overline(x) = 1 / 50
    dot ( 50 dot 15
        + 100 dot 12
        + 150 dot 9
        + 200 dot 7
        + 250 dot 4 ) = 114
$

$
  accent(sigma, ~) = sqrt(1 / 49
    dot ( 50^2 dot 15
        + 100^2 dot 12
        + 150^2 dot 9
        + 200^2 dot 7
        + 250^2 dot 4 )) =\
    = sqrt(18163.26) = 134.77
$

#align(center, [
  #table(
    columns: 9,
    rows: (auto, auto, 23pt, auto),
    table.header(
      table.cell(colspan: 2, rowspan: 2)[*Граница\ интервала*],
      table.cell(rowspan: 2, stroke: (
        bottom: 0pt,
      ))[*Частота\ $n_i$*],
      table.cell(colspan: 2, rowspan: 2)[*Граница\ интервала*],
      table.cell(rowspan: 2, stroke: (
        bottom: 0pt,
      ))[],
      table.cell(rowspan: 2, stroke: (
        bottom: 0pt,
      ))[],
      table.cell(rowspan: 2, stroke: (
        bottom: 0pt,
      ))[],
      table.cell(rowspan: 2, stroke: (
        bottom: 0pt,
      ))[],


      [$x_i$], [ $x_(i + 1)$],
      [],
      [$z_i$], [$z_(i + 1)$],
      [$Phi_(z_i)$], [$Phi_(z_(i + 1))$],
      [$P_i$], [$n dot P_i$],
    ),

    $25$,  $75 $, $15$, $-oo  $, $-0.29$, $-0.5   $, $-0.1141$, $0.3859$, $18.1373$,
    $75$,  $125$, $12$, $-0.29$, $0.08 $, $-0.1141$, $0.0319 $, $0.1460$, $6.862  $,
    $125$, $175$, $9 $, $0.08 $, $0.45 $, $0.0319 $, $0.1736 $, $0.1417$, $6.699  $,
    $175$, $225$, $7 $, $0.45 $, $0.82 $, $0.1736 $, $0.2939 $, $0.1203$, $5.654  $,
    $225$, $275$, $4 $, $0.82 $, $oo   $, $0.2939 $, $0.5    $, $0.2061$, $9.6867 $,
  )
])
// n = 47

#align(center, [
  #table(
    columns: 4,
    rows: (25pt, auto),
    table.header(
      $accent(F, ~) (x)$,
      $accent(F, ~)_n (x)$,
      $|F_0 (x) - accent(F, ~)_n (x)|$,
      $(n_i - n'_i) / n_i$
    ),
    $0.3859$, $0.3 $, $$, $$,
    $0.5319$, $0.54$, $$, $$,
    $0.6736$, $0.72$, $$, $$,
    $0.7939$, $0.86$, $$, $$,
    $1     $, $0.94$, $$, $$,
  )
])
