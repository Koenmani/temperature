const Room_cfg = {
  props: ['item', 'schema'],
  data() {
	  return{
		  isloaded:false,
		  manual: false
	  }
  },
  components: {
	  	 balk: Balk,
	  	 togglebtn: ToggleButton
  },
  computed: {
  	nameString(){
      return this.item.tmp_hand
    }	
  },
  methods: {
	toggle_manual() {
        console.log(this.item.tmp_hand);
        console.log(this.item.ingesteld);
        if (this.item.handmatig == true){ //enable manual control
			// POST /setmanual?tid=xxxxxxxx&manual=on&temp=20.5&time=
			bd = {
				tid: this.item.tid,
				manual: "on",
				temp: this.item.tmp_hand,
				tijd: this.item.volgend_tijd
			}
			
			fetch(this.$root.url+'/setmanual', {method: 'POST',headers: {'Content-Type': 'application/json;charset=utf-8'},body: JSON.stringify(bd)})
			  .then(response => response.json())
			  .then(json => {
					if (json=="done") {
						console.log("yes, it works")
						this.item.ingesteld = this.item.tmp_hand
					}
					else{
						//add class error?
						console.log("fail")
					}
			  })
			  .catch(this.$root.inerror = true);
		}
		else if (this.item.handmatig == false){ //shut down manual control
			// POST /setmanual?tid=xxxxxxxx&manual=on&temp=20.5&time=
			bd = {
				tid: this.item.tid,
				manual: "off",
			}
			
			fetch(this.$root.url+'/setmanual', {method: 'POST',headers: {'Content-Type': 'application/json;charset=utf-8'},body: JSON.stringify(bd)})
			  .then(response => response.json())
			  .then(json => {
					if (json=="done") {
						console.log("yes, it works")
						//this.manual = false
					}
					else{
						//add class error?
						console.log("fail")
					}
			  })
			  .catch(this.$root.inerror = true);
		}
    },
	toggle_vac() {
        console.log(this.item.exclude);
		tmp_exclude = this.item.exclude
			
		fetch(this.$root.url+'/togglevac?room='+this.item.tid, {method: 'GET',headers: {'Content-Type': 'application/json;charset=utf-8'}})
			.then(response => response.json())
			.then(json => {
				if (json=="done") {
					console.log("yes, it works")
					if (tmp_exclude == true){ 
						this.item.exclude = false
					}
					else{
						this.item.exclude = true
					}
				}
				else{
					//add class error?
					console.log("fail")
				}
			})
			.catch(this.$root.inerror = true);
    },
	reset_kamer(){
		this.$parent.activekmr_cfg = 0
	},
	StepUp(){
		this.item.tmp_hand = this.item.tmp_hand + 0.5
		if (this.item.tmp_hand > 30){
			this.item.tmp_hand = 30
		}
	},
	StepDown(){
		this.item.tmp_hand = this.item.tmp_hand - 0.5
		if (this.item.tmp_hand < 5){
			this.item.tmp_hand = 5
		}
	}
  },
  template: `<div class=\"enkele_kamer\">
  				<div class=\"enkele_kamer_tit_wrap\">
					<div class=\"enkele_kamer_title\">{{ item.naam }}</div>
				</div>
				<div class=\"enkele_kamer_terug\" @click=\"reset_kamer\">X</div>
				<div id=\"kamer_sub\" class=\"kamer_sub\">
					<div class=\"kamer_curtemp\">Huidige temp: {{item.huidig}}&#176;</div>
					<div class=\"kamer_newtemp\">Ingestelde temp:{{ item.ingesteld }}&#176;</div>
					<div class=\"kamer_next\">Volgende schakelpunt: {{ item.volgend_tijd }} naar {{ item.volgend_temp }}&#176; </div>
				</div>
				
				<div class=\"kamer_curtemp\">
				<div>Bedien handmatig: 
					<label class="switch">
						<input type="checkbox" v-model="item.handmatig" v-on:change=\"toggle_manual\">
						<span class="slider round"></span>
					</label>
				
					<div class="number-input">
						<button onclick=\"this.parentNode.querySelector('input[type=number]').stepDown()\" @click=\"StepDown\" ></button>
						<input type=\"number\" min=\"5\" max=\"30\" :value=\"nameString\" v-model="item.tmp_hand" step=\"0.5\"></input>&#176;
						<button onclick=\"this.parentNode.querySelector('input[type=number]').stepUp()\" @click=\"StepUp\" class=\"plus\"></button>
					</div>
				
					<div class=\"kamer_curtemp\">Tot volgende schakelpunt </div>
				</div>
				<br/>
				<div class=\"\">Vakantie stand aan/uit 
					<label class="switch">
						<input type="checkbox" v-model="item.exclude" v-on:change=\"toggle_vac\">
						<span class="slider round"></span>
					</label>
				</div>
				<div class=\"\">Kamer offset </div>
				
				
			</div>
		</div>`
}

//kleur oranje of rood toevoegen als een kamer handmatig of op vakantie stand staat
//algemene configuratie toevoegen: algehele vakantiestand aan/uit, smart heating aan/uit, algemene offset
//config knop toevoegen bij kamerbediening