import { Injectable } from '@angular/core';
import { throwError as observableThrowError, Observable } from 'rxjs';
import { catchError, map, delay, retryWhen, take } from 'rxjs/operators';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  options = {
    headers: {
      'Content-Type': 'application/text; charset=utf-8'
    }
  };

  constructor(private http: HttpClient) { }

  GetDiff(): Observable<Array<string>>{
    return this.http.get(
      `${environment.diffLocation}`,
      this.options
    ).pipe(
      map(res => res as Array<string>),
      catchError((err, caught) => this.errorHandling(err, caught))
    )
  }

  // General error handling, just throws the message returned by the API to show to the viewer
  private errorHandling(res, caught) {
    if (res.statusText) {
      console.error('A frontend error occured');
      if (res.name === 'HttpErrorResponse') {

      }
    }
    console.log('The error response: ');
    console.log(res);
    console.log('What was caught:');
    console.log(caught);
    return observableThrowError(res);
  }
}

