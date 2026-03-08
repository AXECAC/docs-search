import docs_parser

# NOTE: все эти точно работают и работают хорошо
# print(docs_parser.get_text("parser/assets/text_and_tables.docx"))
# print(docs_parser.get_text("parser/assets/some_text.docx"))
# print(docs_parser.get_text("parser/assets/text_tables_png.docx"))
# print(docs_parser.get_text("parser/assets/text_from_img.png"))
# print(docs_parser.get_text("parser/assets/main.typ"))
# print(docs_parser.get_text("parser/assets/main.pdf"))
# print(docs_parser.get_text("parser/assets/too_many_png.docx"))
# print(docs_parser.get_text("parser/assets/Presentation.pptx"))
docs_parser.convert_to_new_format("parser/assets/old_docs.doc", "parser/assets/tests_results")
docs_parser.convert_to_new_format("parser/assets/old_pres.ppt", "parser/assets/tests_results")
docs_parser.convert_to_new_format("parser/assets/old_exel.xls", "parser/assets/tests_results")
