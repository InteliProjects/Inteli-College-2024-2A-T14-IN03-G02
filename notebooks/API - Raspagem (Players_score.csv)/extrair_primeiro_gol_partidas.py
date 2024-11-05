
import csv
import requests
import time
import json
import re

# Função para configurar uma sessão com tentativas de repetição
def setup_session_with_retries():
    session = requests.Session()
    retries = requests.adapters.Retry(
        total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    return session

# Função para obter informações dos times (time da casa e time visitante) e dos gols por partida
def get_match_details(match_code):
    base_url = "https://api.fifa.com/api/v3/timelines/2000000078/"
    full_url = f"{base_url}{match_code}&language=pt"  # Monta a URL completa

    session = setup_session_with_retries()

    try:
        response = session.get(full_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Obter nomes dos times da casa e de fora diretamente da API de cada jogo
        home_team = (
            data.get("Home", {})
            .get("TeamName", [{"Description": "Desconhecido"}])[0]
            .get("Description")
        )
        away_team = (
            data.get("Away", {})
            .get("TeamName", [{"Description": "Desconhecido"}])[0]
            .get("Description")
        )

        # Verificar se os dados da partida foram carregados corretamente
        print(f"Partida {match_code}: {home_team} vs {away_team}")

        goals = []
        for event in data.get("Event", []):
            # Verificar se o evento é um gol
            if any(
                type_loc.get("Description") == "Gol!"
                for type_loc in event.get("TypeLocalized", [])
            ):
                description = event.get("EventDescription", [{}])[0].get("Description", "")
                
                # Usar regex para identificar o nome do jogador e o time
                player_name_match = re.search(r"(.*?)\s*\((.*?)\)", description)
                if player_name_match:
                    player_name = player_name_match.group(1)
                    team_name = player_name_match.group(2)
                    match_minute = event.get("Minute", 0)
                    score = (event.get("HomeGoals", 0), event.get("AwayGoals", 0))

                    # Depuração: verificar se as informações de gol estão sendo coletadas corretamente
                    print(
                        f"Gol encontrado: Jogador={player_name}, Time={team_name}, Minuto={match_minute}, Placar={score}"
                    )

                    # Adicionar as informações do gol à lista
                    goals.append(
                        {
                            "player_name": player_name,
                            "team_name": team_name,
                            "match_minute": match_minute,
                            "score": f"{score[0]} - {score[1]}",
                        }
                    )
        return home_team, away_team, goals
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {full_url}: {e}")
        return "Desconhecido", "Desconhecido", []

# Função principal para processar as partidas e salvar no CSV
def main():
    matches_urls = [
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ongcp8i5cmigh47539dpr9jo?date=2024-06-30",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9zt0t2kwqd14n4aij0175idjo?date=2024-07-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a2sxswzolg36f6tpde2si5gr8?date=2024-07-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ai1huef1vxp819nva5o1ulslw?date=2024-08-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9899rxqvxusd6wk0pdewsesyc?date=2024-06-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a8d5x7whnvf1kwfgmh0nurzf8?date=2024-09-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/asuk3i8obk5c3foows4fe05jo?date=2024-08-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8err16hg434tl6fsnvkd5zjf8?date=2024-04-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8y9r18ru7gnxiy2oi3z6ptvkk?date=2024-05-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8s0i2h2gjlw1unfpvrj8jrrbo?date=2024-04-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8wfe6k62b7wvovgb23aqt94wk?date=2024-05-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8l1abyj4mb89webculp9gv384?date=2024-04-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9mfwqf4bbnbahd0rjxclnf8yc?date=2024-06-30",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9rnhagk9baggobcz02e2gwduc?date=2024-07-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8w0jyfgfmbatat2agw3up6ivo?date=2024-08-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ar0dll9lziv6k9krphhfnisyc?date=2024-08-25",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aw8267n4ak580qql40vhk1x5g?date=2024-08-31",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a7zw0px1mlvmmxrevr0vfm3h0?date=2024-07-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a068sit8ppctyt2bycf9szris?date=2024-09-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aqacj6cxbc0pp7pgi51v5lpn8?date=2024-08-18",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/agxdpcqohxr8onw3q163ppzpw?date=2024-08-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8qiwhuqtz4k83y6vcytc85990?date=2024-04-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9471zu995hw2of35krrflbytw?date=2024-06-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aysmum6if0fd6myzlpjn8hno4?date=2024-09-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8kanvakf34rfsatt4624jszkk?date=2024-06-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9se8pfqsm0v1j6834ogxxjhuc?date=2024-07-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/avhqdd9jbetmpf7dzej3ek650?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/awl64l0nproimbb2ytgbnwbo4?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ap4jfkmbalgz2inl2nubb1nv8?date=2024-08-18",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8t3hfx2qmbrqmf121xhh5iuxg?date=2024-05-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a2fr2d8uw49guyz3x2cts1vkk?date=2024-07-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ybu8rfp6cgfel6k77lvs4jys?date=2024-07-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8pfzlhw4q4pr9d2nisc1ok2l0?date=2024-04-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8x5kyms2xx1kjlemiy7uiioes?date=2024-05-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b1fpmgby6z13hh6q7r7omu0wk?date=2024-09-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/azj0rl2obqyzvtggkv50mtbmc?date=2024-09-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8f7tn3iv2x7c2rkcvvp1hpgr8?date=2024-04-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9fafith1pqt8zkyjpcqmmh5w4?date=2024-06-23",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/90412g2fy4gmkmk6ov7gk5a1g?date=2024-06-02",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/91zp0x293nnel2xfvq3msllw4?date=2024-06-02",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8n9ox4x3djbtyoxu6e9ql87pw?date=2024-04-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/91mhc8y76q81eav9ai006dces?date=2024-06-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a93z5r5usduub8zdlkeckyln8?date=2024-07-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ay23l6jkzdxc7izv6280ca5g4?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8uk41vn1mje6eth78y65vlclw?date=2024-05-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/92czdq0y363rvhtjiwzrjvdp0?date=2024-06-02",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9d2wif47gruz83gmjix5plgyc?date=2024-06-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a7movjks11sk5gkteat3euj2s?date=2024-07-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ag6ugiv8scrihf0rtkh9b2uj8?date=2024-08-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ulj8ejcfq8vix3fg92y0j4lw?date=2024-07-06",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8u6zlr0c7l79pebns2rf09st0?date=2024-05-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ac332y1b55bv99eoz4jkntxjo?date=2024-07-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9w3kx4tat3mj268ul0ruqstg4?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a5dgbcnlzdluai37lt9w2sdn8?date=2024-07-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a36777ai2yjef3b50q8enmyac?date=2024-07-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9xl2rewn74ubla7v8jiklnpjo?date=2024-07-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a1brbecd45jbvk67dya4ogufo?date=2024-07-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8opyrlt5g50keo2xedeyt3oyc?date=2024-04-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aa7hej525cznjes3vrzt8ttec?date=2024-07-25",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8jk48bdq56crkidub853gwz6c?date=2024-04-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/98zs3ukecylbsovwdgxc00178?date=2024-06-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/af1azwetcuz0jjqlgoc84wufo?date=2024-07-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/as3ytyr3219uiz1oitn2lyjv8?date=2024-08-25",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8ttrhrz6curqlzcaoir395mhg?date=2024-05-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9fnnnholpwef4vovxgf7c14pg?date=2024-06-23",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b1t41vmkoj260sqvkmtqjxic4?date=2024-09-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8lr7b5k2ldlg9ay9ywuglg2l0?date=2024-04-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ayfaqrlux9mbe7gfu4xbmt990?date=2024-09-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9iay7p24i8e05ltlwya8fidxw?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ra414eix6hp523smik3t9n2s?date=2024-07-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a0ykb4o7mgr5sibc3zwrwvqxg?date=2024-07-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/awydevpkdss04r9khtuszt2qc?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9e6jgl6vwpdripk9a130kxdec?date=2024-06-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9agpqa9efctc0mpw8bqzs4qac?date=2024-06-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/amvozlwp8fvk2jxq3kld3v8yc?date=2024-08-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/am55r9j4pobyand7hl8hlp6hg?date=2024-08-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aho6p3koizwv4h98bm3y8zi1g?date=2024-08-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ggcbaycch4njudt4nxg8dlhw?date=2024-06-23",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/99qafgahe31fhx4fm520or47o?date=2024-06-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8g3sajsin8zmwh34t0cn2xr84?date=2024-04-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9qwyc99dz4on5p5lq0asu3aj8?date=2024-07-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8xwf3hbvmv5u3je77855y6uj8?date=2024-05-12",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8wsf8u4zayk8bxmy6bqzorxg4?date=2024-05-12",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9io2hkddq5sehuh27x0sd7llg?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9m2dz7esj2tzaj11qeeyi385w?date=2024-06-30",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ao09gsfvksd3rh3xqg45t9y50?date=2024-08-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9n6kh7y8orpjz5swz36sl7qc4?date=2024-06-30",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/axbl1q3s2oh1yoxh5txdl8bo4?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a4n3op13pf2wht3t6ftt2u0wk?date=2024-07-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/axow1rwirzzegqocifv9qi7tg?date=2024-08-31",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9s0xz8zqc4s5yzg9hqqmj2978?date=2024-07-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/975rcw8juw9c2xpr3f2wwvac4?date=2024-06-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ex7jzfkid79h0df4v410o2dw?date=2024-06-23",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9njpckxvpzo4dpe909q58rmdw?date=2024-06-29",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9xyjw9s43rymjcx95a5ttqw44?date=2024-07-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/95nghevt0176h5zuoode7lwd0?date=2024-06-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8yn16jebv538a2gys6h5lyu50?date=2024-05-12",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aphrfjua5hgrfxicxc0qtdvkk?date=2024-08-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ais0givft6ih3uua8786a7klw?date=2024-08-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9x7ipfxd9p45p07eplk23v1uc?date=2024-07-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aqn8y1plo4ajlkklgupzdxvdg?date=2024-08-18",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/atyflnua71525n9echirgqqs4?date=2024-08-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8mjg66mfxwnem85kb3nitf6z8?date=2024-04-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/abprg83lt99aqb7ln3v07ugic?date=2024-08-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b12an4r7konj2a0gqbal4k9p0?date=2024-09-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8nzoxw2teakhbe2jh9i0gfx90?date=2024-04-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8mwvsz54aizvwupnnp3cbrpqs?date=2024-04-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a3jfhb5t2j3k0jg5vnjrh87pw?date=2024-07-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aazhpg7705ws9l5w4878e8zys?date=2024-07-23",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9yp6616415wow10s1s1ld8jkk?date=2024-07-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aeap9eh17culprg5cdt0ara50?date=2024-07-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9hxghastklvv07uqzbbg94t90?date=2024-06-22",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a6iqayh8ola61f3by9rjjgges?date=2024-07-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/apv0cyog4h3zf9wn4119tiwic?date=2024-08-18",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ahau8xem0xf6ockbksahzv8yc?date=2024-08-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/alejsd8y85q5bnjlowjy085jo?date=2024-08-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aj58dlyxn08czq1yzbo5hx6vo?date=2024-08-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/933gj15al7drgque412f78yz8?date=2024-06-02",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8qvr8lofhjrtkyrw40tfaz7dg?date=2024-04-29",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/960pwga5dm8f6l3ax2sbu0utw?date=2024-06-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/agk75hocwu52qpfx3qsw1668k?date=2024-08-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9bm1dq1q5u05u7j4uipypmrkk?date=2024-06-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9atybt2vu6so3zdl9qbaitatw?date=2024-06-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/azwid581h1equakz911gwo00k?date=2024-09-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/akztt6yk2tbi9tck35llmb4lw?date=2024-08-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ejxq29hl7z6lepnwfem38nx0?date=2024-06-22",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9pe8l7umiohtzwkv41g96cmc4?date=2024-06-30",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ajimb70urd5w6fgsgfjiqs104?date=2024-08-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/an9ln0a9a6nb0qkys7kee1el0?date=2024-08-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8fnszpcd2tn8tljwwyohrfbbo?date=2024-04-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9a3ju78fykixunqvwma8mhtlg?date=2024-06-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ardi3o3gopgahoh0i4aeesmc4?date=2024-08-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8va96zv76899rjkufo8fg3nkk?date=2024-05-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b09wrup88ah1rurszus915st0?date=2024-09-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8ebuftj9peb1kowus7ihnyh3o?date=2024-04-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/abcjmxk52lh1z5r8mh1br20ic?date=2024-07-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a508gjpexm1ulovd97v8e311w?date=2024-07-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/amievflz4ff83rnagcdv01jpw?date=2024-08-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b2wtd1uf1x4sr73aypnj1twd0?date=2024-09-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9dg5fzi34r6mnpwkxxmjz5kic?date=2024-06-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a794g2yvbxl4o4yjyku98v1n8?date=2024-07-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8zqsskipi1f45lho5ifemomj8?date=2024-06-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9qi4ea9i1pnhksr2y8kjfjjtg?date=2024-07-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9vbtg243ab03itrqlly59j0gk?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b3a186bejl92dthe2eklthbmc?date=2024-09-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ki90dkblc4l5k5rwbha9xkb8?date=2024-06-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8gjuy0ir2yg5fh7vbzgcawdg4?date=2024-04-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9vqivvr1rcjgae1yzmktrahhw?date=2024-07-06",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8gzu8y64jsu69qutnk3lt8a38?date=2024-04-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8igxdzvebucmawf11y38pttzo?date=2024-04-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a3wrg7cw8ps19jbe51sxlafis?date=2024-07-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a9h861235mrf70bi2mtmhgefo?date=2024-07-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8dfywqjbud86zjynvhrn7807o?date=2024-04-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9wu52lhyj0v00tq2xriqxvl78?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9ccetftmuj5fercpzl0f3493o?date=2024-06-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a1p3sgimmehbxlwgg1uqtrqxg?date=2024-07-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9nwy1sh4qoqcai36v4qlpe0b8?date=2024-07-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9u89h1r9ks4pofd2efj80qa6s?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a658j3innjty3dokzcqidlous?date=2024-07-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aupq8kei0k7zxecx0tfohg6j8?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9hk7ipae9dmvjneodlape2x3o?date=2024-06-22",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/actqxu3bxht7r2ym8j94b9t04?date=2024-07-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aoqym8at2czhutrw11kn19pg4?date=2024-08-18",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8q5yf62i5yl0ot4ym0uxd515g?date=2024-04-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8he2cmqed8gwjbq9acnb0zitw?date=2024-04-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8tglqz9xpgdlyi9qxral86wic?date=2024-05-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9thrpvqaluwly1wi1bmmc4844?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8sqhx0tv3zrkhsxdh8odzut5g?date=2024-08-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b0p1zpve58b2x70jzhzhah2qc?date=2024-09-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8le8pwlx5qy8d5u9kb7qzjjtg?date=2024-04-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/afemf5i31n8h5l80kf30o5990?date=2024-07-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8xixiuoh6heddd35z6g9iwkk4?date=2024-05-12",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/93gpr0f7o07sygi5as146oems?date=2024-06-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/akmlpvec5t7y39sktgqsl711w?date=2024-08-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9t4lpb6lfg4n43yn0exnr6bdg?date=2024-07-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8jxlxgtygy822ewf7hg8zu1hw?date=2024-04-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8rnejfgr61rr87y76n4gp14ic?date=2024-04-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8j70te2itnc3j8dc9ixdq3k0k?date=2024-04-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a6vwdfqbgi8dgyzr63ec1yvpw?date=2024-07-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/alrvl63ny8hyp01bbryh07190?date=2024-08-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a49ux9wq873algwev2k4fuxw4?date=2024-07-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ashaual1otvuzhnk0bmsb84yc?date=2024-08-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a22e0dg92xfxdh36d93h60xzo?date=2024-07-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8cwut9j8as00ru27loulqie50?date=2024-04-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/arqn5atwyvesannc0vmmk2rys?date=2024-08-25",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/96fiql81cucmdchgavg43uaz8?date=2024-06-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9uyotthyud3edvmc0phqfy8es?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b40p4gaukuu9y5gd98hytoums?date=2024-09-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/afs14ucprzp7tchqnrbubqyvo?date=2024-08-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/94k6e4yftfqyidayyl2s5sjdg?date=2024-06-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9lp1z860yzsscyant69da1jbo?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9jehqgcu05rtb6v9o6dvuowt0?date=2024-06-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9cpnm7lcewmn9uqh9d3vej7dg?date=2024-06-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aeo1m4gl60dr1hprr5ry04ahg?date=2024-07-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9sre1yngyv6caydkkfc3f43kk?date=2024-07-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8raj02t7swdetk4k77a9qvaqc?date=2024-04-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a5qj9eah9f7sslh411a6e7dhw?date=2024-07-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9p0zq700t1v9ivwi8wn6q77ys?date=2024-06-29",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9g1gni35vvd4ja3vgpsx8lwyc?date=2024-06-22",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9jrkiu82a9hupcbfauaffzytw?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9l9x727ma9des7666tbov9s7o?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/atl4ft5jup9s4mm0b9wxw1rmc?date=2024-08-25",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8nmn1xca5xdo23s4gtb8lls0k?date=2024-04-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/anmwkwmosl9cpi7vanwh5i8t0?date=2024-08-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/99d0r6ocxx3k7muz0fe07dous?date=2024-06-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8zde5p8dh7zrrvdn7p4xx1xqs?date=2024-06-09",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8p2ygrl5ogeyf385asyl6g1lg?date=2024-04-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9j19olx98htqyju2rfq0d5xjo?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9dt9y8y25qgpmjjqrgg3e4a38?date=2024-06-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9z2cmm8ocq1vpqpp18g6lm32s?date=2024-07-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ad6yc7dafv6npo2j4abxio1zo?date=2024-07-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9b78iq61t8g6mnsvymmpxwhlg?date=2024-06-19",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8ko5fgsczi3bo9j9uwqrgw0es?date=2024-04-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/at7tf3153t0mn79yhgk5wjxuc?date=2024-08-25",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9mtcnpxxigti43fua836cij9w?date=2024-06-30",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/96sleul31ydbnpx54a39b66ms?date=2024-06-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aubp69dom7t66d3ym8xn2c8wk?date=2024-08-25",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8vneqtfjwaw4g2rzeh5gqucr8?date=2024-06-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/93ttxgmczbo7rffk2v8uyw74k?date=2024-06-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8hqz32dabb8mv8mahf6w5s3kk?date=2024-04-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/95ael5h7fluxckozkgxke1jbo?date=2024-06-13",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8z07kznmko58udo9ezgyap7v8?date=2024-05-12",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9q4ukdqgpg8j92po7b25ca1hw?date=2024-07-03",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/90h6rndewyn31oaytz67gflec?date=2024-06-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/94xafla94guu5isx3ngzi0e8k?date=2024-06-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9kvoucwetvxv1o1fuxsukgtn8?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aieoisa7cff7qyblknnimsefo?date=2024-08-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a8qjuhuze8zpv1qxo5iaksob8?date=2024-07-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8iu0eu05olzfhw9dtiq6ky13o?date=2024-04-18",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9prpw62gvfistmnrnay5ij504?date=2024-07-04",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/b4rby93ba1lulq4s6c8ynnx1w?date=2024-09-21",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9h6zod70tjpvqavatz0zror2s?date=2024-06-23",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9bz48dmw62ooe5w8k1j59u5uc?date=2024-06-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8m61jm0695di3t1zh1m42ipzo?date=2024-04-20",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/97w523twbfg4ij0jwdjsprmz8?date=2024-06-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/a0jlvazgkqdn9ksz28bzk9yc4?date=2024-07-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/avuv8j7oywvt1aywo0x6ub8k4?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/az5smbqo6fonij8ob30o9uvx0?date=2024-09-15",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/98mkxq34hm0uj19gyeazai68k?date=2024-06-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aakrtff926b8gudoqruclczys?date=2024-07-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/adxaijl6pnl84nqzbiqzmelg4?date=2024-07-27",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8pt0nxerev1jcpayuqh5thxqs?date=2024-04-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/90uqc37ev6mkhw9fwkrrstr10?date=2024-06-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9wgujb3xbyp6pfstyxhgmwu1g?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/acgczj0ajvb7fzn0zjg4zrbis?date=2024-07-28",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/92q8adrl635z5blt4jqz32xp0?date=2024-06-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9oa8z8tgr0486b7f7y73iritw?date=2024-06-30",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8i41gsko2dorr0179s9x25ct0?date=2024-04-16",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ak9a6pwrwk6318tr277ka232s?date=2024-08-11",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8uxa18nrcv5jp17h7hljhej9w?date=2024-05-05",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8octy95gyrhaedmsbax8u1pn8?date=2024-07-24",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/8dvvbzxg9zjllrkmyswjb3rpw?date=2024-04-14",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/919ejpqxqlfa2hwvlygxlp6hg?date=2024-06-02",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/av2ws9x3wo5qf2rffe40wkxec?date=2024-09-01",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9gtkcv57u04p2fhg9bgybaadw?date=2024-06-23",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/97ixm5l16f2fernrqn3wxswt0?date=2024-06-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/ajvwpjgoosejzmtm8rcc48iz8?date=2024-08-10",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9k4t5s923s7ayymv8ogl7rz84?date=2024-06-26",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/9tv1mkywjsy4haxtafu094wes?date=2024-07-07",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/aodiglwne0u3t0uhq7j67khsk?date=2024-08-17",
        "a2yu8vfo8wha3vza31s2o8zkk/a3uw23jicbw0sk41fir9kwnbo/adk4obru5n93xwye1vrofygb8?date=2024-07-27",
    ]


    # Nome do arquivo CSV para salvar os dados
    csv_filename = "goals_data_with_teams.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "event_id",
            "home_team",
            "away_team",
            "player_name",
            "team_name",
            "match_minute",
            "score",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Processa as URLs das partidas
        for match_code in matches_urls:
            # Obtém os times e artilheiros
            home_team, away_team, goals = get_match_details(match_code)

            if not goals:
                print(f"Nenhum gol encontrado para a partida {match_code}")
                continue

            # Pegar apenas o primeiro gol da lista
            first_goal = goals[0]
            print(f"Primeiro gol: Jogador={first_goal['player_name']}, Time={first_goal['team_name']}, Minuto={first_goal['match_minute']}, Placar={first_goal['score']}")

            # Escreve o gol no arquivo CSV
            writer.writerow({
                "event_id": match_code,
                "home_team": home_team,
                "away_team": away_team,
                "player_name": first_goal["player_name"],
                "team_name": first_goal["team_name"],
                "match_minute": first_goal["match_minute"],
                "score": first_goal["score"],
            })

    print(f"Todos os dados foram exportados para {csv_filename}")

if __name__ == "__main__":
    main()