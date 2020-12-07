import {html,PolymerElement} from '/static/otree-redwood/node_modules/@polymer/polymer/polymer-element.js';
import '/static/otree-redwood/node_modules/@polymer/polymer/lib/elements/dom-repeat.js';
import '../polymer-elements/iron-flex-layout-classes.js';
import '../polymer-elements/paper-progress.js';
import '../polymer-elements/paper-radio-button.js';
import '../polymer-elements/paper-radio-group.js';

import '/static/otree-redwood/src/redwood-decision/redwood-decision.js';
import '/static/otree-redwood/src/redwood-period/redwood-period.js';
import '/static/otree-redwood/src/redwood-decision-bot/redwood-decision-bot.js';
import '/static/otree-redwood/src/otree-constants/otree-constants.js';

import '../color.js';

export class RandomNumber extends PolymerElement {
    static get template() {
        return html `
            <style include="iron-flex iron-flex-alignment"></style>
            <style>
                paper-progress {
                    margin-bottom: 10px;
                    --paper-progress-height: 30px;
                }
            </style>
            <otree-constants id="constants"></otree-constants>
            <redwood-period
                running="{{ _isPeriodRunning }}"
                on-period-start="_onPeriodStart"
                on-period-end="_onPeriodEnd">
            </redwood-period>
            
            <redwood-channel
                id="channel"
                channel="number"
                on-event="_handleNumberEvent">
            </redwood-channel>
            <div class="layout vertical center">
                <template is="dom-if" if="{{ _practice }}">
                    <h1> Practice Stage </h1>
                </template>
                        <paper-progress
                            value="[[ _subperiodProgress ]]">
                        </paper-progress>

                        <h1 style="-webkit-touch-callout: none; 
                -webkit-user-select: none; 
                -khtml-user-select: none; 
                -moz-user-select: none; 
                    -ms-user-select: none; 
                        user-select: none; ">[[randomNumber]]</h1>
                        <input id="number" type="text"  required>
                        <button type="button" on-click="_confirm" on-tap="_confirm"> Confirm</button>

            </div>
            
        
        `
    }

    static get properties() {
        return {
            roundNumber:{
                type: Number
            },
            initialNumber:{
                type: Number
            },
            randomNumber:{
                type: Number
            },
            _isPeriodRunning: {
                type: Boolean,
            },
            _subperiodProgress: {
                type: Number,
                value: 0,
            },
            periodLength: {
                type: Number
            },
            timeRemaining:{
                type: Number,
                value: 0,
            }
        }
    }

    ready() {
        super.ready();
        console.log(this.roundNumber);
        this.set("randomNumber", this.initialNumber);
        console.log(this.randomNumber);
    }

    _confirm(){
        if(parseInt(this.shadowRoot.querySelector('#number').value) != this.randomNumber){
            return;
        }
        this.shadowRoot.querySelector('#number').value = '';
        let request = {
            "id": this.$.constants.idInGroup,
            "number": parseInt(this.randomNumber),
        }
        this.$.channel.send(request);
    }

    _handleNumberEvent(event){
        let numberResponse = event.detail.payload;
        if (numberResponse['id'] == this.$.constants.idInGroup) this.set("randomNumber", numberResponse['number']);
    }

    _practice(){
        return parseInt(this.roundNumber) != 1;
    }

    _onPeriodStart() {
        this._subperiodProgress = 0;
        this.lastT = performance.now();
        this._animID = window.requestAnimationFrame(
            this._updateSubperiodProgress.bind(this));
    }
    _onPeriodEnd() {
        window.cancelAnimationFrame(this._animID);
        this._subperiodProgress = 0;
    }
    _updateSubperiodProgress(t) {
        const deltaT = (t - this.lastT);
        const secondsPerSubperiod = this.periodLength / 1;
        this._subperiodProgress = 100 * ((deltaT / 1000) / secondsPerSubperiod);
        this._animID = window.requestAnimationFrame(
            this._updateSubperiodProgress.bind(this));
    }

    _timeRemainingPeriod() {
        if((this.periodLength - this.now ) > 0) {
            return this.periodLength - (this.now );
        }
        else {
            return 0;
        }
    }

    
    
}

window.customElements.define('random-number', RandomNumber);