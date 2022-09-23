const ToggleButton = {
    props: {
        defaultState: {
            type: Boolean, 
            default: false
        }
    },

    data() {
        return {
            manual: false
        }
    },
	methods: {
        toggle_manual() {
            console.log("im here");
        }
    },
    computed: {
        isActive() {
            return this.currentState;
        },

        checkedValue: {
            get() {
                return this.defaultState
            },
            set(newValue) {
                this.currentState = newValue;
                this.$emit('change', newValue);
            }
        }
    },
    //template: `<label for="toggle__button">
    //    <span v-if="isActive" class="toggle__label">On</span>
    //    <span v-if="! isActive" class="toggle__label">Off</span>

    //    <input type="checkbox" id="toggle__button" v-model="checkedValue">
    //    <span class="toggle__switch"></span>
    //</label>`
    template: `
        <label class="switch">
            <input type="checkbox" v-model="manual" v-on:change=\"toggle_manual\">
            <span class="slider round"></span>
        </label>
    `
}