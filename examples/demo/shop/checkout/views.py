from django.shortcuts import render

from oscar.apps.checkout.views import (PaymentMethodView as CorePaymentMethodView, 
                                  PaymentDetailsView as CorePaymentDetailsView,
                                  OrderPreviewView as CoreOrderPreviewView)
from oscar.apps.payment.forms import BankcardForm, BillingAddressForm
from oscar.apps.shipping.methods import ShippingMethod
from oscar.core.loading import import_module
import_module('payment.models', ['Source', 'SourceType'], locals())
import_module('payment.exceptions', ['InvalidBankcardException'], locals())
import_module('payment.utils', ['Bankcard'], locals())    
import_module('payment.datacash.utils', ['Gateway', 'Facade'], locals())
    
class PaymentMethodView(CorePaymentMethodView):
    template_file = 'checkout/payment_method.html'
    
    def handle_GET(self):
        return render(self.request, self.template_file, self.context)
    
    def handle_POST(self):
        method = self.request.POST['method_code']
        self.co_data.pay_by(method)
        return self.get_success_response()
    
    
class OrderPreviewView(CoreOrderPreviewView):
    u"""View a preview of the order before submitting."""
    
    def handle_GET(self):
        # Forward straight onto the payment details - no need for preview
        return self.get_success_response()   
        
        
class PaymentDetailsView(CorePaymentDetailsView):
    template_file = 'checkout/payment_details.html'
    
    def handle_GET(self):
        if self._is_cheque_payment():
            self.template_file = 'checkout/payment_details_cheque.html'
        else:
            shipping_addr = self._get_shipping_address()
            card_values = {'name': shipping_addr.name()}
            self.context['bankcard_form'] = BankcardForm(initial=card_values)
            addr_values = {'first_name': shipping_addr.first_name,
                           'last_name': shipping_addr.last_name,}
            self.context['billing_address_form'] = BillingAddressForm(initial=addr_values)
        return render(self.request, self.template_file, self.context)
    
    def handle_POST(self):
        if self._is_cheque_payment():
            return self.submit()
        try:    
            self.bankcard_form = BankcardForm(self.request.POST)
            self.billing_addr_form = BillingAddressForm(self.request.POST)
            if self.bankcard_form.is_valid() and self.billing_addr_form.is_valid():
                return self.submit()
        except InvalidBankcardException, e:
            self.context['payment_error'] = str(e)
        
        self.context['bankcard_form'] = self.bankcard_form
        self.context['billing_address_form'] = self.billing_addr_form
        return render(self.request, self.template_file, self.context)

    def _handle_payment(self, order_number, total):
        if self._is_cheque_payment():
            self._handle_cheque_payment(total)
        else:    
            self._handle_bankcard_payment(order_number, total)

    def _is_cheque_payment(self):
        payment_method = self.co_data.payment_method()
        return payment_method == 'cheque'

    def _handle_cheque_payment(self):
        # Nothing to do except create a payment source
        type = SourceType.objects.get(code='cheque')
        source = Source(type=type, allocation=total)
        self.payment_sources.append(source)

    def _handle_bankcard_payment(self, order_number, total):
        # Handle payment problems with an exception
        # Make payment submission - handle response from DC
        # - could be an iframe open
        # - could be failure
        # - could be redirect
        
        # Create bankcard object
        bankcard = self.bankcard_form.get_bankcard_obj()
        
        # Handle new card submission (get card_details from self.bankcard)
        dc_facade = Facade()
        reference = dc_facade.debit(order_number, total, bankcard)
        
        # Create payment source
        type,_ = SourceType.objects.get_or_create(name='DataCash', code='datacash')
        source = Source(type=type,
               allocation=total,
               amount_debited=total,
               reference=reference)
        self.payment_sources.append(source)
        
        # Create payment event
        

    def _place_order(self, basket, order_number, total_incl_tax, total_excl_tax):
        order = super(PaymentDetailsView, self)._place_order(basket, order_number, total_incl_tax, total_excl_tax)
        if self._is_cheque_payment():
            # Set order status as on hold
            pass
        return order
