from . import Bot

class Kabum(Bot):
    async def get_prices(self, **kwargs):
        list_prices = [{'name': 'Computador Fácil Completo', 'details': 'Intel Core I7 10700 10ª Geração, 16GB, SSD 480GB, Windows 10 Trial + Monitor 19.5', 'price': '3.686,62'}, {'name': 'Computador Fácil', 'details': 'Intel Core I7 11700 11ª Geração, 16GB Ddr4, SSD 240GB, windows 10 trial', 'price': '3.179,17'}, {'name': 'Computador Fácil Intel Core I7 11700 (11ª Geração)', 'details': '16GB RAM Ddr4, SSD 240GB, 19 Polegadas Led + Teclado E Mouse', 'price': '3.635,88'}, {'name': 'Cooktop 2 Bocas', 'details': 'A Gás, Ferro Fundido, Suggar, Fg2002fvp, 127v', 'price': '309,00'}, {'name': 'Caixa De Som Portátil Daewoo Dw242bk', 'details': 'Boombox, Bluetooth, LED RGB, 100w, 3600 mah, 5 horas de bateria, compatíveis com assistente virtual, Preto e Vermelho', 'price': '546,98'}, {'name': 'Gabinete Gamer Liketec Prime', 'details': 'Mid Tower, RGB, M-ATX e MINI-ITX, Lateral em Acrílico, 1x Cooler Fan, Preto - GL-PRIME-2', 'price': '189,99'}, {'name': 'Notebook Acer Predator Triton Pt316-51s-78v9 I7 12ª Windows 11 Home', 'details': 'RTX 3060 16GB 1TB SSD 16\x94, Wqxga', 'price': '9.499,05'}, {'name': 'All In One Mitsushiba', 'details': '24Polegadas I3-5005u 8g SSD256g, Windows Pro', 'price': '2.462,64'}, {'name': 'All In One 24 Polegadas', 'details': 'Quad Core, N4120 8g, Linux - SSD256G', 'price': '1.951,14'}, {'name': 'Bicicleta Elétrica Moto 500W 48V/23ah Tires 2.5 Mitsushiba', 'details': 'Bicicleta Elétrica Moto 500W 48V/23ah Tires 2.5 Mitsushiba', 'price': '5.942,70'}, {'name': 'All In One Mitsushiba 24 Polegadas', 'details': 'Quad Core, N4120 8g SSD 256, Windows Pro', 'price': '2.044,14'}, {'name': 'Carregador Com Pilhas Aa4', 'details': 'Eneloop 2000 Mah', 'price': '270,00'}, {'name': 'Microfone Sony Ecm-lv1 Original + Extns 5m + P2xp3 + Led', 'details': 'Microfone Sony Ecm-lv1 Original + Extns 5m + P2xp3 + Led', 'price': '329,00'}, {'name': 'Notebook Brazil Pc Intel Quad Core N3450', 'details': '6GB RAM, SSD 64GB, Linux, 14.1 Polegadas, Preto', 'price': '2.128,00'}, {'name': 'Forno Elétrico', 'details': 'Gourmet Grill, Autolimpante 44 Litros - Fischer', 'price': '669,00'}, {'name': 'Computador Elgin E3 Nano N2', 'details': 'Intel Celeron Dual Core, 4GB, SSD 120GB, Preto - 46NN2PC0B8NF', 'price': '1.089,99'}, {'name': 'Computador Concórdia Informática Intel Core i5-10400F', 'details': '8GB, SSD 256GB, Monitor 19.5 + Teclado e Mouse, Linux, Preto - 39768', 'price': '2.799,99'}, {'name': 'PC Gamer Concórdia Informática Intel Core i7-3770', 'details': '16GB, GeForce GTX 1650, SSD 480GB, Monitor 21 + Teclado e Mouse, Linux, Preto - 39767', 'price': '3.499,99'}, {'name': 'Computador Concórdia Informática All In One Intel Core i3-10100', 'details': '8GB, SSD 240GB, Monitor 23.8 Full HD, Linux, Preto - 39769', 'price': '3.099,99'}, {'name': 'Smartphone Samsung Galaxy S23 Ultra 512GB 5g RAM 12GB', 'details': 'Com Caneta S Pen, Câmera Quádrupla 200mp, Selfie 12mp, Tela 6.8 Polegadas, Preto', 'price': '7.599,00'}]
        for i in list_prices:
            i['price'] = i['price'].replace(".", "")
            i['price'] = i['price'].replace(",", ".")

        return list_prices
        #MOCK

        page = self.browser.new_page()
        page.goto(kwargs.get('link'))
        results = []

        #for i in range(5):
        page.wait_for_load_state()
        result = page.evaluate("""
        const produtos = Array.from(document.querySelectorAll('.nameCard'))
        const resultados = []
        produtos.forEach((produto) => {
            const name = produto.innerText.split(',')[0].trim()
            const details = produto.innerText.substr(produto.innerText.indexOf(',') + 1).trim()
            const price = produto.parentElement.parentElement.parentElement.parentElement.querySelector('.priceCard').innerText
            const url = produto.parentElement.parentElement.parentElement.parentElement.parentElement.href
            //const img = produto.parentElement.parentElement.parentElement.parentElement.querySelector("img").src.split('url=')[1]
            resultados.push({name, details, price, url})
        })
        resultados
        """)
        results += result
        
        #next_button_class = """document.querySelector("a[class='nextLink']")"""
        #next_button = page.evaluate(next_button_class)
        #if next_button is None:
        #    break
        
        #next_button = page.evaluate(next_button_class + '.click()')

        return results