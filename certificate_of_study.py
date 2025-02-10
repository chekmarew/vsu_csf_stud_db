import zipfile
import io

# Функция-заглушка
# В production версии идёт обращение к внешнему сервису

def certificate_of_study_file_archive(certificates_of_study, secretary_name=None, file_prefix='', one_file=False):
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "a", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('test.txt', "test")

	zip_bytes.seek(0)
    return zip_bytes
