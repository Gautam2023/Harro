import frappe

def create_description(self, method):
    for_description = [
        "Artikel Bez1",
        "Artikel Bez2",
        "Artikel Bez3",
        "Artikel Bez4",
    ]
    self.desctiption = '<div>'
    for l in for_description:
        fieldname = make_fieldname(l)
        self.description = self.description + "<p>" + self.get(fieldname) + "</p>"

    description += "</div>"



def make_fieldname(label):
    return label.strip().lower().replace(" ", "_") 