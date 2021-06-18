const Room = {
  props: ['item', 'schema'],
  data() {
	  return{
		  isloaded:false
	  }
  },
  components: {
	  	 balk: Balk
  },
  computed: {
  		
  },
  methods: {
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
		this.$parent.activekmr = 0
		this.$root.showpopup = false
		//this.$root.kamer_obj[item.tid].schema[0].temp
	},
	add_temp(dag){
		len = this.schema.length
		
		if (!this.$root.showpopup){
			tijdje = "00:00"
			tempje = 16
			
			tempschema = []
			if ((this.$root.schema_obj.length == 0) || ((this.$root.schema_obj.length <= 1) && (this.$root.schema_obj.dag==null))){
				if (this.$root.schema_obj.length == 0){
					newobj = {
						dag:dag,
						temp:tempje,
						tijd:tijdje
					}
					this.$root.schema_obj.push(newobj)
				}
				index = 0
				if(this.$root.schema_obj[0].dag=="null"){
					this.$root.schema_obj[0].dag=dag
				}
				if(this.$root.schema_obj[0].temp=="null"){
					this.$root.schema_obj[0].temp=tempje
				}
				if(this.$root.schema_obj[0].tijd=="null"){
				 	this.$root.schema_obj[0].tijd=tijdje
				}
			}
			else if (dag == 7){
				var newtime1 = this.$root.schema_obj[this.$root.schema_obj.length-1].tijd.split(":")[0]
				var newtime2 = this.$root.schema_obj[this.$root.schema_obj.length-1].tijd.split(":")[1]
				if (newtime2 == "00"){
					newtime2 = "30"
					if (newtime1 == "24"){
						newtime2 = "00"
					}
					
				}
				else{
					newtime2 = "00"
					newtime1 = parseInt(newtime1) + 1
					if (newtime1 > 24){
						newtime1 = 24
					}
					if (parseInt(newtime1)<10){
						newtime1 = "0" + newtime1
					}			
				}
				tijdje = newtime1+":"+newtime2
				
				newobj = {
					dag:dag,
					temp:this.$root.schema_obj[this.$root.schema_obj.length-1].temp,
					tijd:tijdje
				}
				index = len
				this.$root.schema_obj.push(newobj)
			}
			else {
				found=false
				for (t1=0;t1<len;t1++){
					if ((this.schema[t1].dag > dag) && (found == false)){
						var newtime1 = this.$root.schema_obj[t1-1].tijd.split(":")[0]
						var newtime2 = this.$root.schema_obj[t1-1].tijd.split(":")[1]
						if (newtime2 == "00"){
							newtime2 = "30"
							if (newtime1 == "24"){
								newtime2 = "00"
							}
							
						}
						else{
							newtime2 = "00"
							newtime1 = parseInt(newtime1) + 1
							if (newtime1 > 24){
								newtime1 = 24
							}
							if (parseInt(newtime1)<10){
								newtime1 = "0" + newtime1
							}			
						}
						tijdje = newtime1+":"+newtime2
						
						newobj = {
							dag:dag,
							temp:this.$root.schema_obj[t1-1].temp,
							tijd:tijdje
						}
						
						tempschema.push(newobj)
						index = t1
						tempschema.push(this.schema[t1])
						found = true
					}
					else{
						tempschema.push(this.schema[t1])
					}									
				}
				this.$root.schema_obj = tempschema
			}
			
			
			
			this.$root.old_schema_obj = Object.assign({}, {dag:dag,temp:tempje,tijd:"new"});
		
			this.$root.activeschema = "dag_"+dag+"_tijd_"+index
			this.$root.showpopup = true
			this.$root.popupleft = (event.clientX-200) + "px"
			this.$root.popuptop = (event.clientY-250) + "px"
			//beetje anders bij een nieuw ding
			this.$root.popuparrowleft = (event.clientX + 25) + "px"
			this.$root.popuparrowright = (event.clientX + 85) + "px"
			this.$root.popuparrowtop = (event.clientY - 165) + "px"
			el = document.getElementById("kamer_sub")
			
			w = el.getBoundingClientRect().left + el.getBoundingClientRect().width
			if ((event.clientX - 100 + 300) > w){ //if the popup flies too much to the right (out of bounds)
				this.$root.popupleft = (w - 315) + "px"
			}
			
			
			//this.$root.popuparrowleft = this.$el.getBoundingClientRect().left + this.$el.getBoundingClientRect().width - 35
			//this.$root.popuparrowright = this.$el.getBoundingClientRect().left + this.$el.getBoundingClientRect().width + 10
			//this.$root.popuparrowtop = this.$el.getBoundingClientRect().top
			
		}
		console.log("nieuwe temp toevoegen")
	}
  },
  //template: '<component :item="item" :is="dynamicComponent" />'
  //template: '<component :is="component" :data="data" v-if="component" />'
  //template: "<div :id='tidid' @click=\"this.select_kamer\" v-bind:class=\"[ open_close == true ? 'radactive kamer' : 'radinactive kamer' ]\"><div class=\"kamer_title\">{{ item.naam }}</div><div class=\"kamer_sub\"><div class=\"kamer_curtemp\">{{ item.huidig }}&#176;</div><div class=\"kamer_newtemp\">{{ item.ingesteld }}&#176;</div></div></div>"
  //template: "<div class=\"enkele_kamer\"><div class=\"enkele_kamer_tit_wrap\"><div class=\"enkele_kamer_title\">{{ item.naam }}</div></div><div class=\"enkele_kamer_terug\" @click=\"this.reset_kamer\">X</div><div class=\"kamer_sub\"><div class=\"kamer_curtemp\">Huidige temp: {{item.huidig}}&#176;</div><div class=\"kamer_newtemp\">Ingestelde temp:{{ item.ingesteld }}&#176;</div><div class=\"kamer_next\">Volgende schakelpunt: {{ item.volgend_tijd }} naar {{ item.volgend_temp }}&#176; </div><div class=\"dagtemp_schema_wrapper\"><div class=\"dag_wrapper\"><div class=\"dag_kolom\"></div><div class=\"tempschema\"><div class=\"tempschema_header\"><div class=\"tempschema_header_tijd\">00:00</div></div><div class=\"tempschema_header\"><div class=\"tempschema_header_tijd\">06:00</div></div><div class=\"tempschema_header\"><div class=\"tempschema_header_tijd\">12:00</div></div><div class=\"tempschema_header\"><div class=\"tempschema_header_tijd\">18:00</div></div></div><div class=\"tempschema_controls\"></div></div><div class=\"dag_wrapper\"><div class=\"dag_kolom\">Ma</div><div class=\"tempschema\" v-html=\"balkenschema(1)\" @click=\"this.select_time\"></div><div class=\"tempschema_controls\">+</div></div><div class=\"dag_wrapper\"><div class=\"dag_kolom\">Di</div><div class=\"tempschema\" v-html=\"balkenschema(2)\"></div><div class=\"tempschema_controls\">+</div></div><div class=\"dag_wrapper\"><div class=\"dag_kolom\">Wo</div><div class=\"tempschema\" v-html=\"balkenschema(3)\"></div><div class=\"tempschema_controls\">+</div></div><div class=\"dag_wrapper\"><div class=\"dag_kolom\">Do</div><div class=\"tempschema\" v-html=\"balkenschema(4)\"></div><div class=\"tempschema_controls\">+</div></div><div class=\"dag_wrapper\"><div class=\"dag_kolom\">Vr</div><div class=\"tempschema\" v-html=\"balkenschema(5)\"></div><div class=\"tempschema_controls\">+</div></div><div class=\"dag_wrapper\"><div class=\"dag_kolom\">Za</div><div class=\"tempschema\" v-html=\"balkenschema(6)\"></div><div class=\"tempschema_controls\">+</div></div><div class=\"dag_wrapper\"><div class=\"dag_kolom\">Zo</div><div class=\"tempschema\" v-html=\"balkenschema(7)\"></div><div class=\"tempschema_controls\">+</div></div></div></div></div>"
  template: `<div class=\"enkele_kamer\">
  				<div class=\"enkele_kamer_tit_wrap\">
					<div class=\"enkele_kamer_title\">{{ item.naam }}</div>
				</div>
				<div class=\"enkele_kamer_terug\" @click=\"reset_kamer\">X</div>
				<div id=\"kamer_sub\" class=\"kamer_sub\">
					<div class=\"kamer_curtemp\">Huidige temp: {{item.huidig}}&#176;</div>
					<div class=\"kamer_newtemp\">Ingestelde temp:{{ item.ingesteld }}&#176;</div>
					<div class=\"kamer_next\">Volgende schakelpunt: {{ item.volgend_tijd }} naar {{ item.volgend_temp }}&#176; </div>
					<div class=\"dagtemp_schema_wrapper\">
						<div class=\"dag_wrapper\">
							<div class=\"dag_kolom\"></div>
							<div class=\"tempschema\">
								<div class=\"tempschema_header\">
									<div class=\"tempschema_header_tijd\">00:00</div>
								</div>
								<div class=\"tempschema_header\">
									<div class=\"tempschema_header_tijd\">06:00</div>
								</div>
								<div class=\"tempschema_header\">
									<div class=\"tempschema_header_tijd\">12:00</div>
								</div>
								<div class=\"tempschema_header\">
									<div class=\"tempschema_header_tijd\">18:00</div>
								</div>
							</div>
							<div class=\"tempschema_controls\"></div>
						</div>
						<div class=\"dag_wrapper\">
						<div class=\"dag_kolom\">Ma</div>
						<div class=\"tempschema\"><balk v-for=\"(v, index) in balkenschema(1)\" :item=\"v\" :key=\"index\"></balk></div>
						<div class=\"tempschema_controls\" @click=\"add_temp(1)\">+</div>
					</div>
					<div class=\"dag_wrapper\">
						<div class=\"dag_kolom\">Di</div>
						<div class=\"tempschema\"><balk v-for=\"(v, index) in balkenschema(2)\" :item=\"v\" :key=\"index\"></balk></div>
						<div class=\"tempschema_controls\" @click=\"add_temp(2)\">+</div>
					</div>
					<div class=\"dag_wrapper\">
						<div class=\"dag_kolom\">Wo</div>
						<div class=\"tempschema\"><balk v-for=\"(v, index) in balkenschema(3)\" :item=\"v\" :key=\"index\"></balk></div>
						<div class=\"tempschema_controls\" @click=\"add_temp(3)\">+</div>
					</div>
					<div class=\"dag_wrapper\">
						<div class=\"dag_kolom\">Do</div>
						<div class=\"tempschema\"><balk v-for=\"(v, index) in balkenschema(4)\" :item=\"v\" :key=\"index\"></balk></div>
						<div class=\"tempschema_controls\" @click=\"add_temp(4)\">+</div>
					</div>
					<div class=\"dag_wrapper\">
						<div class=\"dag_kolom\">Vr</div>
						<div class=\"tempschema\"><balk v-for=\"(v, index) in balkenschema(5)\" :item=\"v\" :key=\"index\"></balk></div>
						<div class=\"tempschema_controls\" @click=\"add_temp(5)\">+</div>
					</div>
					<div class=\"dag_wrapper\">
						<div class=\"dag_kolom\">Za</div>
						<div class=\"tempschema\"><balk v-for=\"(v, index) in balkenschema(6)\" :item=\"v\" :key=\"index\"></balk></div>
						<div class=\"tempschema_controls\" @click=\"add_temp(6)\">+</div>
					</div>
					<div class=\"dag_wrapper\">
						<div class=\"dag_kolom\">Zo</div>
						<div class=\"tempschema\"><balk v-for=\"(v, index) in balkenschema(7)\" :item=\"v\" :key=\"index\"></balk></div>
						<div class=\"tempschema_controls\" @click=\"add_temp(7)\">+</div>
					</div>
				</div>
			</div>
		</div>`
}