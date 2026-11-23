Источник истины: model.yaml. Файл ES_velo.drawio генерируется из него, ручные правки
в .drawio при следующей сборке пропадут. Студенты работают в draw.io напрямую, этот
конвейер нужен для эталона.

Сборка (проверено на Linux, draw.io Desktop 31.4.5, PlantUML 1.2026.8, Graphviz 2.43):
  python lint.py                      формулировки по Таблице 1 (нужен pymorphy3)
  python gen_drawio.py                три листа: карта событий, агрегаты, контексты
  python make_print.py                ES_velo_печать_A3.pdf: обзор и 7 листов ленты A3
  python gen_puml.py model.yaml ES_velo_contexts.puml
  python gen_puml.py model.yaml ES_velo_timeline.puml --timeline
  java -DPLANTUML_LIMIT_SIZE=12000 -jar plantuml.jar -tpng -charset UTF-8 ES_velo_timeline.puml

gen_drawio.py не пишет файл, если нашёл ошибку: ссылку на несуществующее событие
или агрегат, два элемента в одной ячейке раскладки, стрелку сквозь чужой стикер,
ключ YAML, прочитанный как логическое значение (on, off, yes, no).

Раскладка задаётся полями col и row. Если две межконтекстные стрелки идут рядом
в одну сторону, канал задаётся явно: route_gap (номер столбца, справа от которого
идёт вертикаль) и route_dx (сдвиг в пикселях).

Печать: на A3 книжной текст стикеров около 7,6 пт, подписи типов около 6,4 пт.
Вся лента на одном листе A4 не читается.
