import docs_parser

# NOTE: все эти точно работают и работают хорошо
# (doc_p, _) = docs_parser.extract_text("parser/assets/text_and_tables.docx")
# (doc_p, _) = docs_parser.extract_text("parser/assets/text_and_tables.docx")
# (doc_p, _) = docs_parser.extract_text("parser/assets/some_text.docx")
# (doc_p, _) = docs_parser.extract_text("parser/assets/text_tables_png.docx")
# (doc_p, _) = docs_parser.extract_text("parser/assets/text_from_img.png")
# (doc_p, _) = docs_parser.extract_text("parser/assets/main.typ")
# (doc_p, _) = docs_parser.extract_text("parser/assets/main.pdf")
# (doc_p, _) = docs_parser.extract_text("parser/assets/too_many_png.docx")
# (doc_p, _) = docs_parser.extract_text("parser/assets/Presentation.pptx")
(doc_p, _) = docs_parser.extract_text("parser/assets/Book.xlsx")
print(doc_p)
# docs_parser.convert_to_new_format("parser/assets/old_docs.doc", "parser/assets/tests_results")
# docs_parser.convert_to_new_format("parser/assets/old_pres.ppt", "parser/assets/tests_results")
# docs_parser.convert_to_new_format("parser/assets/old_exel.xls", "parser/assets/tests_results")
