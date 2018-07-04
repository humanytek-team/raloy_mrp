# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from openerp.exceptions import ValidationError


_ALLOWED_DIFFERENCE = .0000001  # MARGEN PERMITIDO DE DIFERENCIA ENTRE 2 NUMEROS
_ALLOWED_DIFFERENCE_PERC = 0.002


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    move_raw_ids = fields.One2many(
        'stock.move',
        'raw_material_production_id',
        'Raw Materials',
        oldname='move_lines',
        copy=False,
        states={
            'done': [('readonly', True)],
            'cancel': [('readonly', True)]
        },
        domain=[
            ('scrapped', '=', False),
            ('state', '!=', 'cancel')
        ],
    )

    @api.multi
    def _generate_moves(self):
        res = super(MrpProduction, self)._generate_moves()
        for production in self:
            if production.move_raw_ids:
                for move in production.move_raw_ids:
                    # CONTENDRA VALOR ORIGINAL A CONSUMIR (INFORMATIVO)
                    move.product_uom_qty_original = move.product_uom_qty
                    if move.bom_line_id and production.product_id.categ_id.mrp_bom_modification:
                        move.real_p = move.bom_line_id.bom_p

        return res

    def get_min_qty(self, move, production_qty):
        """OBTIENE EL % CORRESPONDIENTE A LA CANTIDAD ESTABLECIDA EN LA LISTA DE MATERIAL."""
        bom_qty = move.bom_line_id.product_qty
        formula_p = round(move.formula_p, 5)
        min_qty = ((bom_qty * formula_p) / 100) * production_qty
        return min_qty

    def check_move_line(self, move):
        if move.obligatorio:
            if move.bom_line_id and not move.new_bom_line and move.raw_material_production_id:
                production_qty = move.raw_material_production_id.product_qty  # 100%
                product_uom_qty = move.product_uom_qty  # ?
                min_qty = self.get_min_qty(move, production_qty)
                if product_uom_qty < min_qty:
                    raise ValidationError(_('La cantidad minima permitida para ' + move.product_id.name + ' es ' + str(min_qty)))
        return

    @api.multi
    def check_percentage(self):
        """REVISA QUE SE CUMPLA LA CONDICION DE 100% DE LISTA DE MATERIALES."""
        for production in self:
            if production.product_id.categ_id and production.product_id.categ_id.mrp_bom_modification:
                # SE OBTIENE EL 100% DE LA LISTA DE MATERIALES ORIGINAL (SUMA DEL TOTAL DE CANTIDADES)
                bom_total = 0
                if production.bom_id and production.bom_id.bom_line_ids:
                    bom_total = sum([((line.product_qty / production.bom_id.product_qty) * production.product_qty)
                                     for line in production.bom_id.bom_line_ids])
                # SE OBTIENE EL 100% DE LOS MATERIALES A CONSUMIR
                production_total = 0
                if production.move_raw_ids:
                    for move in production.move_raw_ids:
                        self.check_move_line(move)
                    production_total = sum([move.product_uom_qty for move in production.move_raw_ids
                                            if move.state not in ('cancel')])
                differencia_perc = bom_total / production_total
                if differencia_perc - 1 > _ALLOWED_DIFFERENCE_PERC:
                    str_differencia = str('{0:f}'.format((1 - differencia_perc) * 100))
                    raise ValidationError(_('No alcanza el 100% de cantidad de produccion necesario' +
                                            '\nTotal Lista de materiales = ' + str(bom_total) +
                                            '\nTotal Materiales a consumir = ' + str(production_total) +
                                            '\nDiferencia porcentual: ' + str(str_differencia)))
    # HEREDA METODOS EXISTENTES Y AGREGA CHECKEO DE PORCENTAGES

    @api.multi
    def button_plan(self):
        if self.state not in ('done', 'cancel', 'progress'):
            self.check_percentage()
        super(MrpProduction, self).button_plan()

    @api.multi
    def action_assign(self):
        if self.state not in ('done', 'cancel', 'progress'):
            self.check_percentage()
        super(MrpProduction, self).action_assign()
