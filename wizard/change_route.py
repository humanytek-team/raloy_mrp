# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from openerp.exceptions import ValidationError


class ChangeProductionRoute(models.TransientModel):
    _name = 'change.production.route'

    mo_id = fields.Many2one(
        'mrp.production',
        'Manufacturing Order',
        required=True,
    )
    routing_id = fields.Many2one(
        'mrp.routing',
        'Ruta de Produccion',
        required=True,
    )

    @api.model
    def default_get(self, fields):
        res = super(ChangeProductionRoute, self).default_get(fields)
        if 'mo_id' in fields and not res.get('mo_id') and self._context.get('active_model') == 'mrp.production' and self._context.get('active_id'):
            res['mo_id'] = self._context['active_id']
        if 'routing_id' in fields and not res.get('routing_id') and res.get('mo_id'):
            res['routing_id'] = self.env['mrp.production'].browse(res['mo_id']).routing_id.id
        return res

    @api.multi
    def change_route(self):
        for wizard in self:
            # REVISAR SI LA NUEVA RUTA CONTIENE EL MISMO NUMERO DE ORDENES DE PRODUCCION
            operation_ids = wizard.mo_id.routing_id and wizard.mo_id.routing_id.operation_ids
            new_operation_ids = wizard.routing_id and wizard.routing_id.operation_ids
            if len(operation_ids) != len(wizard.routing_id.operation_ids):
                raise ValidationError(_('La ruta seleccionada contiene un numero distinto de operaciones'
                                        + ' a la ya establecida en la orden de produccion\nPor favor seleccione otra ruta'))
            # SE ACTUALIZAN LOS CENTROS DE TRABAJO EN LAS ORDENES DE TRABAJO YA CREADAS
            if wizard.mo_id.workorder_ids:
                # SE VALIDA QUE COINCIDAN LOS NOMBRES
                for workorder in wizard.mo_id.workorder_ids:
                    found = False
                    for operation in new_operation_ids:
                        if operation.name == workorder.name:
                            found = True
                    if found is False:
                        raise ValidationError(_('No se encontro operacion en la ruta ' + wizard.routing_id.name + ' que coincida con: ' + workorder.name))
                # SE ACTUALIZAN LOS CENTROS DE PRODUCCION
                for workorder in wizard.mo_id.workorder_ids:
                    for operation in new_operation_ids:
                        if operation.name == workorder.name:
                            workorder.workcenter_id = operation.workcenter_id.id
                            continue
            wizard.mo_id.routing_id = wizard.routing_id.id
