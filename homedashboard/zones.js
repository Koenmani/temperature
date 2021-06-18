function isDefined(x) {
    var undefined;
    return x !== undefined;
}
const Zones = {
  props: ['item', 'type'],
  computed: {
    tijd() {
      if (this.$root.water_obj.watering == true){
		  if (this.$vnode.key == this.$root.water_obj.cur_zone){
		  	return Math.round((this.$root.water_obj.zonetimingleft / 60) * 100) / 100
		  }
		  else{
			return this.item.timing / 60
		  }
	  }
	  else{
		  return this.item.timing / 60
	  }	  
    },
    open_close() {
		if (isDefined(this.item.radiator)){
			if (this.item.radiator[0].open_close == 1){
				return true
			}
			else{
				return false
			}
		}
    }
  },
  methods: {
	wateringstatus(){
		if (this.$root.water_obj.watering == false){
			return 'radinactive kamer'
		}
		else{
			if (this.$root.activeprog == this.$root.water_obj.cur_program+1){
				if (this.$vnode.key == this.$root.water_obj.cur_zone){
					return 'radactive kamer'
				}
				else{
					return 'radinactive kamer'
				}
			}
			else{
				return 'radinactive kamer'
			}
		}
	},
	toggle_zone(){
		if (this.$root.activeprog == 1){ //if this is manual control, start watering
			if (this.$el.classList.contains("radactive")){
				console.log("stop watering zone: "+this.$vnode.key)
				this.$el.classList.remove("radactive")
				fetch(this.$root.ip+'/watering?action=stop&value=0;'+this.$vnode.key)//http://192.168.0.125/watering?action=start&value=0;1
						.then(response => response.json())
						.then(json => {
							this.$root.watering_status = false
							this.$root.water_obj = json
						})
			}
			else{
				if (this.$root.watering_status == false){
					console.log("start watering zone: "+this.$vnode.key)
					this.$el.classList.add("radactive")
					fetch(this.$root.ip+'/watering?action=start&value=0;'+this.$vnode.key)//http://192.168.0.125/watering?action=start&value=0;1
							.then(response => response.json())
							.then(json => {
								this.$root.watering_status = true
								this.$root.water_obj = json
							})
				}
				else{
					//something else first needs to stop?
					
				}
				
			}
			
		}
		else{ //else open screen to edit timing...etc
			
		}	
	}
  },
  template: "<div v-bind:class=\"this.wateringstatus()\" @click=\"this.toggle_zone\"><div class=\"kamer_title\">naam: {{ item.beschrijving }}</div><div>tijd: {{this.tijd}} min</div></div>"
}