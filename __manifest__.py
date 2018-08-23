# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Campos de porcentaje en listas de materiales',
    'version': '1.6.1',
    'author': 'Humanytek',
    'category': 'Mrp',
    'description': """
    Agrega campos de porcentaje en listas de materiales
    de ordenes de produccion
    """,
    'depends': [
        'mrp_add_remove_products',
        'mrp_default_locations',
    ],
    'data': [
        'mrp_view.xml',
        'mrp_workorder.xml',
        'product_view.xml',
        'stock_move_add_view.xml',
        'wizard/change_route_view.xml',
    ],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
