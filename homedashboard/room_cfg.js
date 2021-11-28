const Room_cfg = {
  props: ['item', 'schema'],
  data() {
	  return{
		  isloaded:false
	  }
  },
  components: {
	  	 balk: Balk,
	  	 togglebtn: ToggleButton
  },
  computed: {
  		
  },
  methods: {
	toggle_manual(value) {
        console.log(value);
        if (value == true){
			// POST /setmanual?tid=xxxxxxxx&manual=on&temp=20.5&time=
			bd = {
				tid: this.item.tid,
				manual: "on",
				temp: this.item.ingesteld,
				time: this.item.volgend_tijd
			}
			
			fetch(this.$root.url+'/setmanual', {method: 'POST',headers: {'Content-Type': 'application/json;charset=utf-8'},body: JSON.stringify(bd)})
			  .then(response => response.json())
			  .then(json => {
					if (json['result']=="done") {
						console.log("yes, it works")
					}
					else{
						//add class error?
						console.log("fail")
					}
			  })
			  .catch(this.$root.inerror = true);
		}
		else if (value == false){
			// POST /setmanual?tid=xxxxxxxx&manual=on&temp=20.5&time=
			bd = {
				tid: this.item.tid,
				manual: "off",
			}
			
			fetch(this.$root.url+'/setmanual', {method: 'POST',headers: {'Content-Type': 'application/json;charset=utf-8'},body: JSON.stringify(bd)})
			  .then(response => response.json())
			  .then(json => {
					if (json['result']=="done") {
						console.log("yes, it works")
					}
					else{
						//add class error?
						console.log("fail")
					}
			  })
			  .catch(this.$root.inerror = true);
		}
    },
	processdag(dag){
		result = []
		t1 = 0
		vorigetemp = 0
		vorigetijd = 0
		l = 0
		w = 0
		len = this.schema.length		
		vorigetemp = parseFloat(this.schema[len-1].temp)
		for (t1=0;t1<len;t1++){
			if (this.schema[t1].dag == dag){
				//calculate integer from the timing and divide by 
				if (parseInt(this.schema[t1].tijd.split(":")[1]) == 30){
					decimals = 0,5
				}
				else{
					decimals = 0
				}
				l = vorigetijd
				w = (parseInt(this.schema[t1].tijd.split(":")[0])+decimals)*(100/24) - l
				if (vorigetemp <= 16){
					c = "#FFF"
				}
				else if (vorigetemp <= 20){
					c = "#228B22"
				}
				else if (vorigetemp > 20){
					c = "#FF8C00"
				}
				else{
					c = "#FFF"
				}
				result.push({'l':l, 'c': c, 'id': "dag_"+dag+"_tijd_"+t1, 'w':w, 'temp':this.schema[t1].temp})
			}
			vorigetemp = parseFloat(this.schema[t1].temp)
			l = l + w
			vorigetijd = l
		}
		return result
	},	
	balkenschema: function(dag) {
		undef = undefined
		gotit = false
		if (this.schema!=undef){
			return this.processdag(dag)
		}
		else{
			fetch(this.$root.url+'/kamerschema?nr='+this.item.tid)
			.then(response => response.json())
			.then(json => {
				this.schema = json
				len = this.schema.length
				return this.processdag(dag)
			})
		}
    },
	reset_kamer(){
		this.$parent.activekmr_cfg = 0
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
				
				<div class=\"kamer_curtemp\"><div>Bedien handmatig: </div><togglebtn v-on:change="toggle_manual"></togglebtn>&#176;</div><div class=\"kamer_curtemp\">Tot volgende schakelpunt </div>
				<div class=\"\">Vakantie stand aan/uit </div>
				<div class=\"\">Kamer offset </div>
				
				
			</div>
		</div>`
}

//kleur oranje of rood toevoegen als een kamer handmatig of op vakantie stand staat
//algemene configuratie toevoegen: algehele vakantiestand aan/uit, smart heating aan/uit, algemene offset
//config knop toevoegen bij kamerbediening