{
    'name': "Cyber Maintenance",
    'summary': "Mở rộng chức năng Maintenance Request cho Cyber Game",
    'description': """
        Module này kế thừa và mở rộng model maintenance.request,
        thêm các trường và logic đặc thù cho Cyber Game.
    """,
    'author': "Toan Nguyen",
    'category': 'Maintenance',
    'version': '1.0',
    'depends': ['maintenance', 'base', 'product'],  
    'data': [
        'views/cyber_maintenance_views.xml',
        'views/cyber_maintenance_team_views.xml',
        'views/cyber_expense_views.xml',
        'views/cyber_expense_type_views.xml',  
        'security/ir.model.access.csv',  
    ],
    'installable': True,
    'application': True,
}
