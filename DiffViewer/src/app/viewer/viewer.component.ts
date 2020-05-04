import { Component, OnInit } from '@angular/core';
import { timer } from 'rxjs';

import { ApiService } from '../api.service';

@Component({
  selector: 'app-viewer',
  templateUrl: './viewer.component.html',
  styleUrls: ['./viewer.component.scss']
})
export class ViewerComponent implements OnInit {
  diff = ''
  diffTimer;
  // How often, in miliseconds, the server should be checked
  refreshInterval = 60000;

  constructor(private apiService: ApiService) {
  }

  ngOnInit(): void {
    // Setup the timer. Call GetAutoCADStatus()
    this.diffTimer = timer(0, this.refreshInterval);
    this.diffTimer.subscribe(t => this.LoadDiff());
  }

  LoadDiff() {
    this.apiService.GetDiff()
      .subscribe(res => {
        this.diff = '<pre><code class="diff highlight">'
        res.forEach(line => {
          this.diff += line + '\n';
        })
        this.diff += '</code></pre>'
      });
  }

}
