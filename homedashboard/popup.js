const Popup = {
  props: ['kmr', 'tijd', 'popupx', 'popupy'],
  computed: {
   	temp(){
		key = parseInt(this.tijd.split("_")[3])
		len = this.$root.schema_obj.length
		if (key == 0){
			return this.$root.schema_obj[len-1].temp
		}
		else{
			return this.$root.schema_obj[key-1].temp
		}
	},
  },
  methods: {
	show_dag(){
		dag = this.tijd.split("_")[1]
		if (dag==1){
			return "Maandag"
		}
		else if (dag==2){
			return "Dinsdag"
		}
		else if (dag==3){
			return "Woensdag"
		}
		else if (dag==4){
			return "Donderdag"
		}
		else if (dag==5){
			return "Vrijdag"
		}
		else if (dag==6){
			return "Zaterdag"
		}
		else if (dag==7){
			return "Zondag"
		}
	},
	hide_popup(){
		key = parseInt(this.tijd.split("_")[3])
		//this.$root.schema_obj[key].tijd = Object.assign({}, this.$root.old_schema_obj.tijd);
		if (this.$root.old_schema_obj.tijd == "new"){
			this.$root.schema_obj.splice(key,1)
			this.$root.old_schema_obj = null
			this.$root.showpopup = false
		}
		else{
			this.$root.schema_obj[key].tijd = this.$root.old_schema_obj.tijd.slice()
			if (key == 0){
				key = len-1
			}
			else{
				key = key-1
			}
			this.$root.schema_obj[key].temp = this.$root.old_temp_obj
			this.$root.old_schema_obj = null
			this.$root.showpopup = false
		}
	},
	opslaan_tijd(){
		//key = parseInt(this.tijd.split("_")[3])
		//len = this.$root.schema_obj.length
		//dag = this.$root.schema_obj[key].dag
		//for (t1=0;t1<len;t1++){
		//	if (this.$root.schema_obj[t1].dag == dag){
		//	}
		//}
		
		//bd = {
		//	kmrnr: this.$root.activekmr,
		//	obj: this.$root.schema_obj
		//}
		key = parseInt(this.tijd.split("_")[3])
		len = this.$root.schema_obj.length
		if (key == 0){
			k = len-1
		}
		else{
			k=key-1
		}
		bd = {
			kmrnr: this.$root.activekmr,
			sid:this.$root.schema_obj[k].sid,
			obj: this.$root.schema_obj[k]
		}
		fetch(this.$root.url+'/setschedule', {method: 'POST',headers: {'Content-Type': 'application/json;charset=utf-8'},body: JSON.stringify(bd)})
			  .then(response => response.json())
			  .then(json => {
					if (json['result']=="done") {
						this.$root.old_schema_obj = null
						this.$root.showpopup = false
						this.$root.schema_obj[k].sid = json['sid']
						this.$root.inerror = false
					}
					else{
						//add class error?
						this.$root.inerror = true
					}
			  })
			  .catch(this.$root.inerror = true);
		
		if (this.$root.schema_obj[k].dag != this.$root.schema_obj[key].dag){
			var tmpsid = this.$root.schema_obj[k].sid
			var tmpobj = this.$root.schema_obj[k]
		}
		else{
			var tmpsid = this.$root.schema_obj[key].sid
			var tmpobj = this.$root.schema_obj[key]
		}
		bd = {
				kmrnr: this.$root.activekmr,
				sid:tmpsid,
				obj: tmpobj
		}
		fetch(this.$root.url+'/setschedule', {method: 'POST',headers: {'Content-Type': 'application/json;charset=utf-8'},body: JSON.stringify(bd)})
			  .then(response => response.json())
			  .then(json => {
					if (json['result']=="done") {
						this.$root.old_schema_obj = null
						this.$root.showpopup = false
						this.$root.schema_obj[key].sid = json['sid']
						this.$root.inerror = false
					}
					else{
						//add class error?
						this.$root.inerror = true
					}
			  })
			  .catch(this.$root.inerror = true);
	},
	del_tijd(){
		key = parseInt(this.tijd.split("_")[3])
		//len = this.$root.schema_obj.length
		//dag = this.$root.schema_obj[key].dag
		//for (t1=0;t1<len;t1++){
		//	if (this.$root.schema_obj[t1].dag == dag){
		//	}
		//}
		len = this.$root.schema_obj.length
		if (key == 0){
			k = len-1
		}
		else{
			k=key-1
		}
		if (this.$root.schema_obj[k].dag != this.$root.schema_obj[key].dag){
			var tmpsid = this.$root.schema_obj[k].sid
		}
		else{
			var tmpsid = this.$root.schema_obj[key].sid
		}
		bd = {
			kmrnr: this.$root.activekmr,
			sid:tmpsid,
			obj: null
		}
		fetch(this.$root.url+'/setschedule', {method: 'POST',headers: {'Content-Type': 'application/json;charset=utf-8'},body: JSON.stringify(bd)})
			.then(response => response.json())
			.then(json => {
					if (json['result']=="done") {
						this.$root.old_schema_obj = null
						this.$root.showpopup = false
						this.$root.inerror = false
						this.$root.schema_obj.splice(key,1)
					}
					else{
						//add class error?
						this.$root.inerror = true
					}
			})
			.catch(this.$root.inerror = true);
		
	},
	van_tijd(){
		if (this.$root.old_schema_obj.tijd == "new"){
			return "nieuw"
		}
		else{
			key = parseInt(this.tijd.split("_")[3])
			len = this.$root.schema_obj.length
			if (key == 0){
			 	k = len-1
			}
			else{
				k=key-1
			}
			if (this.$root.schema_obj[k].dag != this.$root.schema_obj[key].dag){
				if (this.$root.schema_obj[k].dag==1){
					dag = "Ma"
				}
				else if (this.$root.schema_obj[k].dag==2){
					dag = "Di"
				}
				else if (this.$root.schema_obj[k].dag==3){
					dag = "Wo"
				}
				else if (this.$root.schema_obj[k].dag==4){
					dag = "Do"
				}
				else if (this.$root.schema_obj[k].dag==5){
					dag = "Vr"
				}
				else if (this.$root.schema_obj[k].dag==6){
					dag = "Za"
				}
				else if (this.$root.schema_obj[k].dag==7){
					dag = "Zo"
				}
				return "("+dag+") "+ this.$root.schema_obj[k].tijd
			}
			else{
				return this.$root.schema_obj[k].tijd
			}
		}	
	},
	tot_tijd(){
		key = parseInt(this.tijd.split("_")[3])
		return this.$root.schema_obj[key].tijd
	},
	
	temp_down(){
		key = parseInt(this.tijd.split("_")[3])
		if (key == 0){
			key = len-1
		}
		else{
			key = key-1
		}
		len = this.$root.schema_obj.length
		this.$root.schema_obj[key].temp = parseFloat(this.$root.schema_obj[key].temp) - 0.5
		if (parseFloat(this.$root.schema_obj[key].temp) < 5){
			this.$root.schema_obj[key].temp = 5
		}
	},
	temp_up(){
		key = parseInt(this.tijd.split("_")[3])
		if (key == 0){
			key = len-1
		}
		else{
			key = key-1
		}
		len = this.$root.schema_obj.length
		this.$root.schema_obj[key].temp = parseFloat(this.$root.schema_obj[key].temp) + 0.5
		if (parseFloat(this.$root.schema_obj[key].temp) > 30){
			this.$root.schema_obj[key].temp = 30
		}
	},
	time_down(){
		key = parseInt(this.tijd.split("_")[3])
		if (this.$root.schema_obj[key].tijd == "null"){
			var newtime1 = "00"
			var newtime2 = "00"
		}
		else{
			var newtime1 = this.$root.schema_obj[key].tijd.split(":")[0]
			var newtime2 = this.$root.schema_obj[key].tijd.split(":")[1]
		}
		if (newtime2 == "00"){
			newtime2 = "30"
			if (newtime1 == "00"){
				newtime2 = "00"
			}
			newtime1 = parseInt(newtime1) - 1
			if (newtime1 < 0){
				newtime1 = 0
			}
			if (parseInt(newtime1)<10){
				newtime1 = "0" + newtime1
			}
		}
		else{
			newtime2 = "00"
			
		}
		newtime = newtime1+":"+newtime2
		
		key2 = key - 1
		if (key2<0){
			key2 = len-1
		}
		var a = new Date();
		var b = new Date();
		a.setHours(parseInt(newtime1),parseInt(newtime2))
		b.setHours(parseInt(this.$root.schema_obj[key2].tijd.split(":")[0]),parseInt(this.$root.schema_obj[key2].tijd.split(":")[1]))
		if ((parseInt(this.tijd.split("_")[1])!=parseInt(this.$root.schema_obj[key2].dag)) || (key==key2)){
			this.$root.schema_obj[key].tijd = newtime
		}
		else if ((a > b) || (this.$root.schema_obj[key].tijd == "null")){
			this.$root.schema_obj[key].tijd = newtime
		}
		else{
			this.$root.schema_obj[key].tijd = this.$root.schema_obj[key].tijd
		}		
	},
	time_up(){
		key = parseInt(this.tijd.split("_")[3])
		if (this.$root.schema_obj[key].tijd == "null"){
			var newtime1 = "00"
			var newtime2 = "00"
		}
		else{
			var newtime1 = this.$root.schema_obj[key].tijd.split(":")[0]
			var newtime2 = this.$root.schema_obj[key].tijd.split(":")[1]
		}
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
		newtime = newtime1+":"+newtime2
		
		key2 = key + 1
		if (key2>=this.$root.schema_obj.length){
			key2 = 0
		}
		var a = new Date();
		var b = new Date();
		a.setHours(parseInt(newtime1),parseInt(newtime2))
		b.setHours(parseInt(this.$root.schema_obj[key2].tijd.split(":")[0]),parseInt(this.$root.schema_obj[key2].tijd.split(":")[1]))
		if ((parseInt(this.tijd.split("_")[1])!=parseInt(this.$root.schema_obj[key2].dag)) || (key==key2)){
			this.$root.schema_obj[key].tijd = newtime
		}
		else if ((a < b) || (this.$root.schema_obj[key].tijd == "null")){
			this.$root.schema_obj[key].tijd = newtime
		}
		else{
			this.$root.schema_obj[key].tijd = this.$root.schema_obj[key].tijd
		}
	}
  },
  template: `<div ref='noclick'>
  				<div class=\"popup_wrapper\" :class=\"[ this.$root.inerror === true ? 'error' : '' ]\" v-bind:style=\"{left: popupx, top: popupy}\">
	  				<div class=\"popuptitle\">{{this.show_dag()}}
	  				</div>
	  				<div @click=\"hide_popup()\" class=\"popup_hide\">X</div>
				  	<div class=\"popup_text\">Van: {{this.van_tijd()}}</div>
				  	<div class=\"popup_text\">Tot: {{this.tot_tijd()}}</div>
				  	<div @click=\"btn_temp_up_down()\" class=\"popup_text\">Temp: {{this.temp}}&#176;</div>
					<div v-if="this.van_tijd() != 'nieuw'" @click=\"del_tijd()\" class=\"popup_acties\">(del)</div>
				  	<div @click=\"opslaan_tijd()\" class=\"popup_acties\">(opslaan)</div>
				  	<div class="popup_temp_plus" @click=\"temp_up()\"></div>
					<div class="popup_temp_min" @click=\"temp_down()\"></div>
				</div>
				<div class="popup_arrow_left" v-bind:style=\"{left: this.$root.popuparrowleft, top: this.$root.popuparrowtop}\" @click=\"time_down()\"></div>
				<div class="popup_arrow_right" v-bind:style=\"{left: this.$root.popuparrowright, top: this.$root.popuparrowtop}\" @click=\"time_up()\"></div>
			</div>`
}