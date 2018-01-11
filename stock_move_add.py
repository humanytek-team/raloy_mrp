# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, RedirectWarning, ValidationError

#PARA FECHAS
from datetime import datetime, timedelta

#OTROS
import openerp.addons.decimal_precision as dp

##### SOLUCIONA CUALQUIER ERROR DE ENCODING (CARACTERES ESPECIALES)
import sys
reload(sys)  
sys.setdefaultencoding('utf8')

class StockMoveAdd(models.TransientModel):
    _inherit = "stock.move.add"

    routing_id = fields.Many2one('mrp.routing', 'Routing',required=True)
    operation_id = fields.Many2one('mrp.routing.workcenter', 'Consumido en operacion', required=True)
    mo_id = fields.Many2one('mrp.production', 'Manufacturing Order', required=True)


    @api.model
    def default_get(self, fields):
        #print fields
        res = super(StockMoveAdd, self).default_get(fields)
        if 'mo_id' in fields and not res.get('mo_id') and self._context.get('active_model') == 'mrp.production' and self._context.get('active_id'):
            res['mo_id'] = self._context['active_id']
            if 'routing_id' in fields and not res.get('routing_id') and self._context.get('active_model') == 'mrp.production' and self._context.get('active_id'):
                routing_id = self.env['mrp.production'].browse(res['mo_id']).routing_id.id
                res['routing_id'] = routing_id
        return res


    def add_production_consume_line(self, new_move, production):
        #print 'add_production_consume_line'
        move_id = super(StockMoveAdd,self).add_production_consume_line(new_move,production)
        #print 'move_id: ',move_id

        #SE AGREGA OPERACION
        #print 'self.operation_id.id: ',self.operation_id.id
        move_id.operation_id = self.operation_id.id
        #print 'move_id.operation_id: ',move_id.operation_id
        #CALCULA PORCENTAJE DEL TOTAL PARA NUEVO MATERIAL A CONSUMIR
        if move_id.state in ('cancel',):
            move_id.porcentaje = 0
        else:
            bom_total = move_id.get_bom_total()
            if bom_total > 0 and move_id.state not in ('cancel'):
               move_id.porcentaje = (move_id.product_uom_qty * 100) / bom_total

        #CALCULA UNIT FACTOR
        original_quantity = move_id.raw_material_production_id.product_qty - move_id.raw_material_production_id.qty_produced
        if original_quantity > 0:
            move_id.unit_factor = (move_id.product_uom_qty / original_quantity)

        #SE CALCULA EL %REAL
        production_qty = production.product_qty
        real_p = 0
        if production_qty > 0:
            real_p = (move_id.product_uom_qty * 100) / production_qty
        move_id.real_p = real_p

        return move_id


    #SOBRESCRITURA DE METODO ORIGINAL PARA CALCULAR EL #_REAL CUANDO SE AGREGA AUN PRODUCTO YA EXISTENTE
    def add_mo_product(self):
        """ Add new move.
        @return: True.
        """        
        if self.env.context is None:
            self.env.context = {}
        
        if not self.env.context.get('mo_id', False) or not self.env.context.get('active_id', False) :
            raise osv.except_osv(_('Exception!'), _('Can not create the Move related to MO'))
        
        new_move = self.browse(self.ids)[0]
        
        mrp_obj = self.env['mrp.production']
        production = mrp_obj.browse(self.env.context.get('mo_id', False) or self.env.context.get('active_id', False))
  
        found = False
        for move in production.move_raw_ids:
            if (move.product_id.id == new_move.product_id.id) and (move.state not in ('cancel','done')):
                if move.procure_method != 'make_to_order': #SI ES BAJO PEDIDO SE TIENE QUE AGREGAR EN OTRA LINEA, NO LA MISMA
                    qty_in_line_uom = self.product_qty
 

                    old_move = self.env['stock.move'].browse(move.id)
                    new_qty = old_move.product_qty + new_move.product_qty
                    #vals={'product_uom_qty': move.product_qty + qty_in_line_uom,'unit_factor': new_qty / (production.product_qty - production.qty_produced)}

                    #NUEVO EN SOBRESCRITURA#####
                    #SE CALCULA real_p
                    real_p = 0
                    if production.product_qty > 0:
                        real_p = ( (move.product_qty + qty_in_line_uom) *  100) / production.product_qty
                    vals={'real_p':real_p,'product_uom_qty': move.product_qty + qty_in_line_uom,'unit_factor': new_qty / (production.product_qty - production.qty_produced)}
                    #############################


                    self.env['stock.move'].browse(move.id).write(vals)
                    found = True
                    break
        consume_move_id = False
        if not found:
            #print 'NOT FOUND'
            consume_move_id = self.add_production_consume_line(new_move, production)
            #print 'consume_move_id, ',consume_move_id


        return True

